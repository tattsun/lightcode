"""UI display functions."""

import json

from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme

# Custom theme
custom_theme = Theme({
    "tool.name": "bold cyan",
    "tool.index": "dim",
    "success": "green",
    "error": "bold red",
    "warning": "yellow",
    "muted": "dim",
})

console = Console(theme=custom_theme)

# Display limits
MAX_RESULT_LINES = 5
MAX_LINE_LENGTH = 80


def format_image_attachments(images: list) -> str:
    """Format image attachment info for display.

    Args:
        images: List of ClipboardImage objects

    Returns:
        Formatted string showing attachment count
    """
    if not images:
        return ""
    count = len(images)
    if count == 1:
        return "[success]📎 1 image attached[/]"
    return f"[success]📎 {count} images attached[/]"


def truncate_result(result: str) -> str:
    """Truncate tool result for display."""
    lines = result.split("\n")
    truncated_lines = []

    for line in lines[:MAX_RESULT_LINES]:
        if len(line) > MAX_LINE_LENGTH:
            truncated_lines.append(line[: MAX_LINE_LENGTH - 3] + "...")
        else:
            truncated_lines.append(line)

    output = "\n".join(truncated_lines)
    if len(lines) > MAX_RESULT_LINES:
        output += f"\n... ({len(lines) - MAX_RESULT_LINES} more lines)"

    return output


def format_arguments(arguments: dict) -> Syntax:
    """Format arguments as syntax-highlighted JSON."""
    json_str = json.dumps(arguments, ensure_ascii=False, indent=2)
    return Syntax(json_str, "json", theme="monokai", line_numbers=False)


def render_tool_header(name: str, index: int, total: int) -> Text:
    """Render tool header as rich text."""
    text = Text()
    text.append("🔧 ", style="bold")
    text.append(name, style="tool.name")
    text.append(f"  ({index}/{total})", style="tool.index")
    return text


def render_result(result: str, is_error: bool = False) -> Panel:
    """Render tool result as a panel."""
    truncated = truncate_result(result)
    style = "red" if is_error else "green"
    icon = "❌" if is_error else "✅"

    return Panel(
        Text(truncated),
        title=f"{icon} Result",
        title_align="left",
        border_style=style,
        padding=(0, 1),
    )


class _EscPressed(Exception):
    """Internal exception for Esc key press."""

    pass


def request_permission(name: str, arguments: dict, index: int, total: int) -> bool | None:
    """Request user permission for tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments
        index: Current tool index
        total: Total number of tools

    Returns:
        True if allowed, False if denied, None if interrupted (Esc pressed).
    """
    console.print()

    # Header
    header = render_tool_header(name, index, total)

    # Arguments panel
    args_syntax = format_arguments(arguments)

    # Display panel
    console.print(Panel(
        args_syntax,
        title=header,
        title_align="left",
        border_style="yellow",
        subtitle="⚠️  Permission Required",
        subtitle_align="right",
    ))

    # Create key bindings with Esc support
    bindings = KeyBindings()

    @bindings.add("escape")
    def _(event):
        raise _EscPressed()

    while True:
        try:
            answer = pt_prompt(
                "Allow execution? [y/n]: ",
                key_bindings=bindings,
            ).strip().lower()
        except _EscPressed:
            return None
        except (EOFError, KeyboardInterrupt):
            return None

        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        console.print("[warning]Please answer y or n[/]")
