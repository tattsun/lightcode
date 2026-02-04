"""Simple REPL loop with LiteLLM and Tool Calling support."""

import argparse
import json
import os
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, TypeVar

import litellm
from prompt_toolkit import prompt as pt_prompt
from rich.markdown import Markdown
from rich.panel import Panel

from lightcode.interrupt import InterruptHandler, InterruptRequested
from lightcode.logging import append_log
from lightcode.registry import ToolRegistry, execute_tool
from lightcode.tools import ALL_TOOLS, WebFetchTool, WebSearchTool
from lightcode.ui import console

T = TypeVar("T")


# Regex pattern to detect image content in tool results
IMAGE_PATTERN = re.compile(r"^\[IMAGE:([^:]+):(.+)\]$")


def parse_tool_result(result: str) -> str | dict:
    """Parse tool result and convert image content to multimodal format.

    Args:
        result: Raw tool result string

    Returns:
        Either the original string or a dict with multimodal content
    """
    match = IMAGE_PATTERN.match(result)
    if match:
        mime_type = match.group(1)
        base64_data = match.group(2)
        # Return multimodal content format
        return {
            "type": "image",
            "mime_type": mime_type,
            "base64_data": base64_data,
        }
    return result


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------


@dataclass
class ReplConfig:
    """Configuration for the REPL loop."""

    model: str
    registry: ToolRegistry
    instructions: str
    skip_permission: bool
    log_file: Path | None


@dataclass
class ApiCallResult:
    """Unified result from API call."""

    assistant_content: str | None = None
    tool_calls: list[dict] = field(default_factory=list)
    reasoning_summary: str | None = None  # Responses API only


# -----------------------------------------------------------------------------
# API Client Protocol and Implementations
# -----------------------------------------------------------------------------


class ApiClient(ABC):
    """Abstract base class for API clients."""

    @abstractmethod
    def get_status_text(self) -> str:
        """Return status text to display before user input."""
        ...

    @abstractmethod
    def call(self, user_input: str | list) -> ApiCallResult:
        """Make an API call and return unified result."""
        ...

    @abstractmethod
    def add_tool_result(self, tool_call_id: str, result: str | dict) -> None:
        """Add a tool result for the next API call.

        Args:
            tool_call_id: The ID of the tool call
            result: Either a string result or a dict with multimodal content
        """
        ...

    @abstractmethod
    def get_pending_tool_outputs(self) -> list[dict] | None:
        """Get pending tool outputs for Responses API, or None for Completion API."""
        ...

    @abstractmethod
    def log_user_input(self, user_input: str) -> None:
        """Log the user input."""
        ...

    @abstractmethod
    def reset_context(self) -> None:
        """Reset conversation context after interrupt."""
        ...


class CompletionClient(ApiClient):
    """Client for Chat Completions API."""

    def __init__(self, config: ReplConfig):
        self.config = config
        self.model_info = litellm.get_model_info(config.model)
        self.max_tokens = self.model_info.get("max_input_tokens", 128_000)
        self.messages: list[dict] = [
            {"role": "system", "content": config.instructions},
        ]

    def get_status_text(self) -> str:
        token_count = litellm.token_counter(model=self.config.model, messages=self.messages)
        percentage = token_count * 100 // self.max_tokens
        return f"[muted]{self._format_tokens(token_count)} / {self._format_tokens(self.max_tokens)} tokens ({percentage}%)[/]"

    def _format_tokens(self, n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    def call(self, user_input: str | list) -> ApiCallResult:
        # For Completion API, user_input is always a string
        if isinstance(user_input, str):
            user_message = {"role": "user", "content": user_input}
            self.messages.append(user_message)
            if self.config.log_file:
                append_log(self.config.log_file, user_message)

        response = litellm.completion(
            model=self.config.model,
            messages=self.messages,
            tools=self.config.registry.get_schemas(),
        )

        choice = response.choices[0]
        assistant_message = choice.message

        assistant_dict = assistant_message.model_dump()
        self.messages.append(assistant_dict)
        if self.config.log_file:
            append_log(self.config.log_file, assistant_dict)

        result = ApiCallResult()
        if assistant_message.content:
            result.assistant_content = assistant_message.content

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                result.tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments),
                })

        return result

    def add_tool_result(self, tool_call_id: str, result: str | dict) -> None:
        # Handle multimodal content (images)
        if isinstance(result, dict) and result.get("type") == "image":
            mime_type = result["mime_type"]
            base64_data = result["base64_data"]
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_data}",
                        },
                    },
                ],
            }
        else:
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result,
            }
        self.messages.append(tool_message)
        if self.config.log_file:
            append_log(self.config.log_file, tool_message)

    def get_pending_tool_outputs(self) -> list[dict] | None:
        return None  # Completion API doesn't use this pattern

    def log_user_input(self, user_input: str) -> None:
        # For Completion API, logging is done in call() method
        pass

    def reset_context(self) -> None:
        # For Completion API, remove the last assistant message with tool_calls
        # and any tool messages that follow
        while self.messages and self.messages[-1].get("role") == "tool":
            self.messages.pop()
        if self.messages and self.messages[-1].get("role") == "assistant":
            if self.messages[-1].get("tool_calls"):
                self.messages.pop()


class ResponsesClient(ApiClient):
    """Client for Responses API."""

    def __init__(self, config: ReplConfig, reasoning_effort: str):
        self.config = config
        self.reasoning_effort = reasoning_effort
        self.previous_response_id: str | None = None
        self.pending_tool_outputs: list[dict] = []

    def get_status_text(self) -> str:
        return "[muted]Ready[/]"

    def _serialize_output(self, output: list) -> list[dict]:
        """Serialize Responses API output for logging."""
        serialized = []
        for item in output:
            item_type = getattr(item, "type", None)
            if item_type == "reasoning":
                summary = getattr(item, "summary", None)
                summary_texts = []
                if summary:
                    summary_texts = [s.text for s in summary if hasattr(s, "text")]
                serialized.append({"type": "reasoning", "summary": summary_texts})
            elif item_type == "function_call":
                serialized.append({
                    "type": "function_call",
                    "name": getattr(item, "name", ""),
                    "arguments": getattr(item, "arguments", ""),
                    "call_id": getattr(item, "call_id", ""),
                })
            elif item_type == "message":
                content = getattr(item, "content", [])
                texts = [c.text for c in content if hasattr(c, "text")]
                serialized.append({"type": "message", "content": texts})
        return serialized

    def call(self, user_input: str | list) -> ApiCallResult:
        response = litellm.responses(
            model=self.config.model,
            input=user_input,
            instructions=self.config.instructions,
            tools=self.config.registry.get_responses_schemas(),
            previous_response_id=self.previous_response_id,
            reasoning={"effort": self.reasoning_effort, "summary": "auto"},
        )

        self.previous_response_id = response.id

        if self.config.log_file:
            append_log(self.config.log_file, {
                "response_id": response.id,
                "output": self._serialize_output(response.output),
            })

        result = ApiCallResult()
        self.pending_tool_outputs = []

        for item in response.output:
            item_type = getattr(item, "type", None)

            if item_type == "reasoning":
                summary = getattr(item, "summary", None)
                if summary:
                    summary_text = "\n".join(
                        s.text for s in summary if hasattr(s, "text")
                    )
                    if summary_text:
                        result.reasoning_summary = summary_text

            elif item_type == "function_call":
                func_name = getattr(item, "name", "unknown")
                func_args_str = getattr(item, "arguments", "{}")
                call_id = getattr(item, "call_id", "")

                try:
                    func_args = json.loads(func_args_str)
                except json.JSONDecodeError:
                    func_args = {}

                result.tool_calls.append({
                    "id": call_id,
                    "name": func_name,
                    "arguments": func_args,
                })

            elif item_type == "message":
                content = getattr(item, "content", [])
                for c in content:
                    if hasattr(c, "text") and c.text:
                        result.assistant_content = c.text

        return result

    def add_tool_result(self, tool_call_id: str, result: str | dict) -> None:
        # Handle multimodal content (images)
        if isinstance(result, dict) and result.get("type") == "image":
            mime_type = result["mime_type"]
            base64_data = result["base64_data"]
            # For Responses API, use input_image type
            self.pending_tool_outputs.append({
                "type": "function_call_output",
                "call_id": tool_call_id,
                "output": [
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{base64_data}",
                    },
                ],
            })
        else:
            self.pending_tool_outputs.append({
                "type": "function_call_output",
                "call_id": tool_call_id,
                "output": result,
            })

    def get_pending_tool_outputs(self) -> list[dict] | None:
        if self.pending_tool_outputs:
            return self.pending_tool_outputs
        return None

    def log_user_input(self, user_input: str) -> None:
        if self.config.log_file:
            append_log(self.config.log_file, {"role": "user", "content": user_input})

    def reset_context(self) -> None:
        # Clear pending tool outputs and reset context
        # We must reset previous_response_id because the API expects tool outputs
        # for any function calls in the previous response
        self.pending_tool_outputs = []
        self.previous_response_id = None


# -----------------------------------------------------------------------------
# Interrupt Support
# -----------------------------------------------------------------------------


def run_with_interrupt(
    func: Callable[[], T],
    handler: InterruptHandler,
    check_interval: float = 0.1,
) -> T:
    """Run function with interrupt support.

    Runs the given function in a background thread while monitoring for
    interrupts. The caller should have already called handler.monitor_keys().

    Args:
        func: The function to run
        handler: Interrupt handler for coordination
        check_interval: How often to check for interrupts (seconds)

    Returns:
        The result of the function

    Raises:
        InterruptRequested: If user requests interruption
        Exception: Any exception raised by the function
    """
    result_container: dict = {"result": None, "error": None}
    done = threading.Event()

    def worker():
        try:
            result_container["result"] = func()
        except Exception as e:
            result_container["error"] = e
        finally:
            done.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    # Wait for completion while checking for interrupts
    while not done.is_set():
        if handler.is_interrupted():
            raise InterruptRequested()
        done.wait(timeout=check_interval)

    if result_container["error"]:
        raise result_container["error"]

    return result_container["result"]


SYSTEM_PROMPT = """\
You are lightcode, a coding agent that helps users with software engineering tasks.

## Guidelines
- Use tools to read files before modifying them.
- Make minimal, focused changes. Do not add unnecessary code.
- Verify your changes work before reporting completion.
- If a task is unclear, ask for clarification.

## Working Directory
You are working in: {cwd}
"""


def build_agents_md_message(cwd: Path) -> str | None:
    """Load AGENTS.md and build a Codex-style message."""
    agents_md = cwd / "AGENTS.md"
    if not agents_md.exists():
        return None

    content = agents_md.read_text(encoding="utf-8")

    return f"""\
# AGENTS.md instructions for {cwd}

<INSTRUCTIONS>
{content}
</INSTRUCTIONS>
"""


# -----------------------------------------------------------------------------
# Unified REPL Loop
# -----------------------------------------------------------------------------


def run_repl_loop(client: ApiClient, config: ReplConfig) -> None:
    """Run the unified REPL loop with any API client."""
    interrupt_handler = InterruptHandler()

    # Start monitoring for Ctrl-C and Esc for the entire REPL session
    with interrupt_handler.monitoring():
        while True:
            try:
                # Reset interrupt state at the start of each turn
                interrupt_handler.reset()

                console.print(client.get_status_text())

                user_input = pt_prompt("> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ("exit", "quit"):
                    print("Goodbye!")
                    break

                client.log_user_input(user_input)
                current_input: str | list = user_input
                interrupted = False

                while True:
                    try:
                        with console.status("[bold blue]Thinking...", spinner="dots"):
                            result = run_with_interrupt(
                                lambda ci=current_input: client.call(ci),
                                interrupt_handler,
                            )
                    except InterruptRequested:
                        console.print("\n[warning][Interrupted][/]")
                        interrupted = True
                        break

                    # Display reasoning summary (Responses API only)
                    if result.reasoning_summary:
                        console.print()
                        console.print(Panel(
                            Markdown(result.reasoning_summary),
                            title="🧠 Thinking",
                            title_align="left",
                            border_style="dim",
                            style="dim",
                            padding=(0, 1),
                        ))

                    # Handle tool calls
                    if result.tool_calls:
                        total = len(result.tool_calls)
                        tool_interrupted = False

                        for i, tool_call in enumerate(result.tool_calls, start=1):
                            try:
                                tool_result = execute_tool(
                                    config.registry,
                                    tool_call["name"],
                                    tool_call["arguments"],
                                    i,
                                    total,
                                    skip_permission=config.skip_permission,
                                    interrupt_handler=interrupt_handler,
                                )
                            except InterruptRequested:
                                console.print("\n[warning][Interrupted][/]")
                                tool_interrupted = True
                                break

                            # Parse tool result for multimodal content (images)
                            parsed_result = parse_tool_result(tool_result)
                            client.add_tool_result(tool_call["id"], parsed_result)

                        if tool_interrupted:
                            interrupted = True
                            break

                        # Check if we need to continue with tool outputs (Responses API)
                        pending_outputs = client.get_pending_tool_outputs()
                        if pending_outputs is not None:
                            current_input = pending_outputs
                        # For Completion API, just continue the loop
                        continue

                    # Display assistant response
                    if result.assistant_content:
                        console.print()
                        console.print(Panel(
                            Markdown(result.assistant_content),
                            title="🤖 Assistant",
                            title_align="left",
                            border_style="blue",
                            padding=(0, 1),
                        ))
                        console.print()
                    break

                # If interrupted, reset context and continue to next user input
                if interrupted:
                    client.reset_context()
                    continue

            except KeyboardInterrupt:
                console.print("\n[muted]Goodbye![/]")
                break
            except EOFError:
                console.print("\n[muted]Goodbye![/]")
                break
            except Exception as e:
                console.print(f"\n[error]Error: {e}[/]\n")


def run_repl(
    *,
    skip_permission: bool = False,
    enable_web_search: bool = False,
    log_file: Path | None = None,
    api_mode: str = "responses",
    reasoning_effort: str = "medium",
) -> None:
    """Start the REPL."""
    model = os.environ.get("LIGHTCODE_MODEL", "openai/gpt-5.2")

    api_label = "Responses API" if api_mode == "responses" else "Completions API"
    console.print()
    console.print(Panel(
        f"[bold]lightcode REPL[/] [dim]({model} + {api_label})[/]",
        border_style="blue",
    ))
    if skip_permission:
        console.print("[warning]⚡ --no-permissions mode: skipping tool permission prompts[/]")
    if enable_web_search:
        console.print("[success]🌐 Web search enabled (Tavily)[/]")
    if api_mode == "responses":
        console.print(f"[success]🧠 Reasoning effort: {reasoning_effort}[/]")
    if log_file:
        console.print(f"[success]📝 Logging to: {log_file}[/]")
    console.print("[muted]Type 'exit' or 'quit' to exit[/]")
    console.print()

    # Build tool list
    tools = list(ALL_TOOLS)
    if enable_web_search:
        tools.append(WebSearchTool())
        tools.append(WebFetchTool())
    registry = ToolRegistry(tools)

    # Set up system prompt
    cwd = Path.cwd()
    instructions = SYSTEM_PROMPT.format(cwd=cwd)

    # Load AGENTS.md
    agents_message = build_agents_md_message(cwd)
    if agents_message:
        instructions += "\n\n" + agents_message
        console.print("[success]📋 Loaded AGENTS.md[/]")

    # Create configuration
    config = ReplConfig(
        model=model,
        registry=registry,
        instructions=instructions,
        skip_permission=skip_permission,
        log_file=log_file,
    )

    # Create API client and run the loop
    if api_mode == "responses":
        client: ApiClient = ResponsesClient(config, reasoning_effort)
    else:
        client = CompletionClient(config)

    run_repl_loop(client, config)


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="lightcode REPL")
    parser.add_argument(
        "--no-permissions",
        action="store_true",
        help="Skip permission prompts for tool execution",
    )
    parser.add_argument(
        "--web-search",
        action="store_true",
        help="Enable web search tools (requires TAVILY_API_KEY)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Save session log to JSONL file",
    )
    parser.add_argument(
        "--api",
        choices=["completion", "responses"],
        default="responses",
        help="API mode: 'completion' (legacy) or 'responses' (default, with reasoning)",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=["low", "medium", "high"],
        default="medium",
        help="Set reasoning effort level for Responses API (default: medium)",
    )
    args = parser.parse_args()

    run_repl(
        skip_permission=args.no_permissions,
        enable_web_search=args.web_search,
        log_file=args.log_file,
        api_mode=args.api,
        reasoning_effort=args.reasoning_effort,
    )


if __name__ == "__main__":
    main()
