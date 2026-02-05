"""Subagent execution logic."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import litellm

from lightcode.ui import console, truncate_result

if TYPE_CHECKING:
    from lightcode.interrupt import InterruptHandler
    from lightcode.tools.base import Tool


# Regex pattern to detect image content in tool results
IMAGE_PATTERN = re.compile(r"^\[IMAGE:([^:]+):(.+)\]$")


def _parse_tool_result_for_responses(result: str) -> str | list:
    """Parse tool result and convert image content for Responses API.

    Args:
        result: Raw tool result string

    Returns:
        Either the original string or a list with multimodal content
    """
    match = IMAGE_PATTERN.match(result)
    if match:
        mime_type = match.group(1)
        base64_data = match.group(2)
        # Return Responses API format for images
        return [
            {
                "type": "input_image",
                "image_url": f"data:{mime_type};base64,{base64_data}",
            },
        ]
    return result


def _parse_tool_result_for_completion(result: str) -> str | list:
    """Parse tool result and convert image content for Completion API.

    Args:
        result: Raw tool result string

    Returns:
        Either the original string or a list with multimodal content
    """
    match = IMAGE_PATTERN.match(result)
    if match:
        mime_type = match.group(1)
        base64_data = match.group(2)
        # Return Completion API format for images
        return [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_data}",
                },
            },
        ]
    return result


SUBAGENT_SYSTEM_PROMPT = """\
You are a subagent of lightcode, a coding agent that helps users with software engineering tasks.

## Your Role
You are a specialized {subagent_type} subagent. {description}

## Guidelines
- Focus on completing the assigned task efficiently.
- Use the available tools to accomplish your task.
- Report your findings and results clearly.
- If you cannot complete the task, explain why.

## Working Directory
You are working in: {cwd}

## Task
{task}
"""


def _format_args_brief(args: dict) -> str:
    """Format arguments briefly for display."""
    parts = []
    for key, value in args.items():
        if isinstance(value, str):
            if len(value) > 50:
                value = value[:47] + "..."
            parts.append(f'{key}="{value}"')
        elif isinstance(value, (int, float, bool)):
            parts.append(f"{key}={value}")
        else:
            parts.append(f"{key}=...")
    return ", ".join(parts)


def _print_subagent_status(turn: int, message: str) -> None:
    """Print subagent status with turn indicator."""
    console.print(f"  [dim]↳ [Turn {turn}] {message}[/]")


def _print_subagent_tool(turn: int, name: str, args: dict) -> None:
    """Print subagent tool call."""
    args_brief = _format_args_brief(args)
    console.print(f"  [dim]↳ [Turn {turn}] [cyan]{name}[/]({args_brief})[/]")


def _print_subagent_result(result: str, is_error: bool = False) -> None:
    """Print subagent tool result briefly."""
    truncated = truncate_result(result)
    # Indent each line
    lines = truncated.split("\n")
    style = "red" if is_error else "green"
    for line in lines[:3]:  # Show max 3 lines
        console.print(f"  [dim]   → [{style}]{line}[/][/]")
    if len(lines) > 3:
        console.print(f"  [dim]   → ... ({len(lines) - 3} more lines)[/]")


def run_subagent(
    *,
    subagent_type: str,
    task: str,
    context: str,
    description: str,
    model: str,
    tools: list[Tool],
    api_mode: str,
    reasoning_effort: str,
    max_turns: int,
    interrupt_handler: InterruptHandler | None,
) -> str:
    """Run a subagent with independent context.

    Args:
        subagent_type: Name of the subagent type.
        task: Task description for the subagent.
        context: Additional context for the task.
        description: Description of the subagent type.
        model: Model to use.
        tools: List of available tools for this subagent type.
        api_mode: API mode ('completion' or 'responses').
        reasoning_effort: Reasoning effort level for Responses API.
        max_turns: Maximum number of turns before stopping.
        interrupt_handler: Optional interrupt handler.

    Returns:
        Final result from the subagent.
    """
    # Import here to avoid circular imports
    from lightcode.registry import ToolRegistry

    # Build system prompt
    cwd = Path.cwd()
    full_task = task
    if context:
        full_task = f"{task}\n\n## Additional Context\n{context}"

    instructions = SUBAGENT_SYSTEM_PROMPT.format(
        subagent_type=subagent_type,
        description=description,
        cwd=cwd,
        task=full_task,
    )

    # Create tool registry for this subagent
    registry = ToolRegistry(tools)

    # Run the subagent loop
    if api_mode == "responses":
        return _run_responses_subagent(
            model=model,
            instructions=instructions,
            registry=registry,
            reasoning_effort=reasoning_effort,
            max_turns=max_turns,
            interrupt_handler=interrupt_handler,
        )
    else:
        return _run_completion_subagent(
            model=model,
            instructions=instructions,
            registry=registry,
            max_turns=max_turns,
            interrupt_handler=interrupt_handler,
        )


def _run_completion_subagent(
    *,
    model: str,
    instructions: str,
    registry: ToolRegistry,
    max_turns: int,
    interrupt_handler: InterruptHandler | None,
) -> str:
    """Run subagent using Chat Completions API."""
    from lightcode.interrupt import InterruptRequested, run_with_interrupt

    messages: list[dict] = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": "Please complete the task described above."},
    ]

    last_content: str | None = None

    for turn in range(1, max_turns + 1):
        # Check for interrupt
        if interrupt_handler and interrupt_handler.is_interrupted():
            raise InterruptRequested()

        _print_subagent_status(turn, "Thinking...")

        # Run API call with interrupt support
        if interrupt_handler:
            response = run_with_interrupt(
                lambda: litellm.completion(
                    model=model,
                    messages=messages,
                    tools=registry.get_schemas(),
                ),
                interrupt_handler,
            )
        else:
            response = litellm.completion(
                model=model,
                messages=messages,
                tools=registry.get_schemas(),
            )

        choice = response.choices[0]
        assistant_message = choice.message
        messages.append(assistant_message.model_dump())

        # Check for content
        if assistant_message.content:
            last_content = assistant_message.content

        # Handle tool calls
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                # Check for interrupt before each tool
                if interrupt_handler and interrupt_handler.is_interrupted():
                    raise InterruptRequested()

                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                _print_subagent_tool(turn, func_name, func_args)

                try:
                    result = registry.execute(
                        func_name,
                        func_args,
                        interrupt_handler=interrupt_handler,
                    )
                    _print_subagent_result(result)
                except Exception as e:
                    result = f"Error: {type(e).__name__}: {e}"
                    _print_subagent_result(result, is_error=True)

                # Parse result for multimodal content (images)
                parsed_result = _parse_tool_result_for_completion(result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": parsed_result,
                })
            continue

        # No tool calls, done
        _print_subagent_status(turn, "Done")
        break

    return last_content or "Subagent completed without response."


def _run_responses_subagent(
    *,
    model: str,
    instructions: str,
    registry: ToolRegistry,
    reasoning_effort: str,
    max_turns: int,
    interrupt_handler: InterruptHandler | None,
) -> str:
    """Run subagent using Responses API."""
    from lightcode.interrupt import InterruptRequested, run_with_interrupt

    previous_response_id: str | None = None
    current_input: str | list = "Please complete the task described above."
    last_content: str | None = None

    for turn in range(1, max_turns + 1):
        # Check for interrupt
        if interrupt_handler and interrupt_handler.is_interrupted():
            raise InterruptRequested()

        _print_subagent_status(turn, "Thinking...")

        # Run API call with interrupt support
        if interrupt_handler:
            response = run_with_interrupt(
                lambda ci=current_input, pid=previous_response_id: litellm.responses(
                    model=model,
                    input=ci,
                    instructions=instructions,
                    tools=registry.get_responses_schemas(),
                    previous_response_id=pid,
                    reasoning={"effort": reasoning_effort, "summary": "auto"},
                ),
                interrupt_handler,
            )
        else:
            response = litellm.responses(
                model=model,
                input=current_input,
                instructions=instructions,
                tools=registry.get_responses_schemas(),
                previous_response_id=previous_response_id,
                reasoning={"effort": reasoning_effort, "summary": "auto"},
            )

        previous_response_id = response.id
        tool_outputs: list[dict] = []

        for item in response.output:
            item_type = getattr(item, "type", None)

            if item_type == "function_call":
                # Check for interrupt before each tool
                if interrupt_handler and interrupt_handler.is_interrupted():
                    raise InterruptRequested()

                func_name = getattr(item, "name", "unknown")
                func_args_str = getattr(item, "arguments", "{}")
                call_id = getattr(item, "call_id", "")

                try:
                    func_args = json.loads(func_args_str)
                except json.JSONDecodeError:
                    func_args = {}

                _print_subagent_tool(turn, func_name, func_args)

                try:
                    result = registry.execute(
                        func_name,
                        func_args,
                        interrupt_handler=interrupt_handler,
                    )
                    _print_subagent_result(result)
                except Exception as e:
                    result = f"Error: {type(e).__name__}: {e}"
                    _print_subagent_result(result, is_error=True)

                # Parse result for multimodal content (images)
                parsed_result = _parse_tool_result_for_responses(result)
                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": parsed_result,
                })

            elif item_type == "message":
                content = getattr(item, "content", [])
                for c in content:
                    if hasattr(c, "text") and c.text:
                        last_content = c.text

        # If there were tool calls, continue with outputs
        if tool_outputs:
            current_input = tool_outputs
            continue

        # No tool calls, done
        _print_subagent_status(turn, "Done")
        break

    return last_content or "Subagent completed without response."
