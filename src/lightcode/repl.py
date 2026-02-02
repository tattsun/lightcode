"""Simple REPL loop with LiteLLM and Tool Calling support."""

import argparse
import json
import os
from pathlib import Path

import litellm
from prompt_toolkit import prompt as pt_prompt
from rich.markdown import Markdown
from rich.panel import Panel

from lightcode.logging import append_log
from lightcode.registry import ToolRegistry, execute_tool
from lightcode.tools import ALL_TOOLS, WebFetchTool, WebSearchTool
from lightcode.ui import console

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


def run_repl(
    *,
    skip_permission: bool = False,
    enable_web_search: bool = False,
    log_file: Path | None = None,
) -> None:
    """Start the REPL."""
    model = os.environ.get("LIGHTCODE_MODEL", "gpt-5.2")

    console.print()
    console.print(Panel(
        f"[bold]lightcode REPL[/] [dim]({model} + Tool Calling)[/]",
        border_style="blue",
    ))
    if skip_permission:
        console.print("[warning]⚡ --no-permissions mode: skipping tool permission prompts[/]")
    if enable_web_search:
        console.print("[success]🌐 Web search enabled (Tavily)[/]")
    if log_file:
        console.print(f"[success]📝 Logging to: {log_file}[/]")
    console.print("[muted]Type 'exit' or 'quit' to exit[/]")
    console.print()

    # Build tool list
    tools = list(ALL_TOOLS)
    if enable_web_search:
        tools.append(WebSearchTool())
        tools.append(WebFetchTool())
    model_info = litellm.get_model_info(model)
    max_tokens = model_info.get("max_input_tokens", 128_000)
    registry = ToolRegistry(tools)

    # Set up system prompt
    cwd = Path.cwd()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT.format(cwd=cwd)},
    ]

    # Load AGENTS.md as user message if exists
    agents_message = build_agents_md_message(cwd)
    if agents_message:
        messages.append({"role": "user", "content": agents_message})
        console.print("[success]📋 Loaded AGENTS.md[/]")

    def format_tokens(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    while True:
        try:
            # Display status line
            token_count = litellm.token_counter(model=model, messages=messages)
            percentage = token_count * 100 // max_tokens
            console.print(f"[muted]{format_tokens(token_count)} / {format_tokens(max_tokens)} tokens ({percentage} %)[/]")

            user_input = pt_prompt("> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            user_message = {"role": "user", "content": user_input}
            messages.append(user_message)
            if log_file:
                append_log(log_file, user_message)


            # Send request to LLM with tools
            while True:
                with console.status("[bold blue]Thinking...", spinner="dots"):
                    response = litellm.completion(
                        model=model,
                        messages=messages,
                        tools=registry.get_schemas(),
                    )

                choice = response.choices[0]
                assistant_message = choice.message

                # Add message to history
                assistant_dict = assistant_message.model_dump()
                messages.append(assistant_dict)
                if log_file:
                    append_log(log_file, assistant_dict)

                # Check for tool calls
                if assistant_message.tool_calls:
                    total = len(assistant_message.tool_calls)
                    for i, tool_call in enumerate(assistant_message.tool_calls, start=1):
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)

                        result = execute_tool(
                            registry,
                            func_name,
                            func_args,
                            i,
                            total,
                            skip_permission=skip_permission,
                        )

                        # Add tool result
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                        messages.append(tool_message)
                        if log_file:
                            append_log(log_file, tool_message)
                    # Call LLM again with tool results
                    continue
                else:
                    # No tool calls, display response
                    if assistant_message.content:
                        console.print()
                        console.print(Panel(
                            Markdown(assistant_message.content),
                            title="🤖 Assistant",
                            title_align="left",
                            border_style="blue",
                            padding=(0, 1),
                        ))
                        console.print()
                    break

        except KeyboardInterrupt:
            console.print("\n[muted]Goodbye![/]")
            break
        except EOFError:
            console.print("\n[muted]Goodbye![/]")
            break
        except Exception as e:
            console.print(f"\n[error]Error: {e}[/]\n")


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
    args = parser.parse_args()

    run_repl(
        skip_permission=args.no_permissions,
        enable_web_search=args.web_search,
        log_file=args.log_file,
    )


if __name__ == "__main__":
    main()
