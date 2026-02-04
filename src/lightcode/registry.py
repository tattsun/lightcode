"""Tool registration and management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from lightcode.tools import Tool
from lightcode.ui import (
    console,
    format_arguments,
    render_result,
    render_tool_header,
    request_permission,
)

if TYPE_CHECKING:
    from lightcode.interrupt import InterruptHandler


class ToolRegistry:
    """Tool registration and management."""

    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def get_schemas(self) -> list[dict]:
        """Get schemas for all tools (Chat Completions API format)."""
        return [tool.to_schema() for tool in self._tools.values()]

    def get_responses_schemas(self) -> list[dict]:
        """Get schemas for all tools (Responses API format)."""
        schemas = []
        for tool in self._tools.values():
            schema = tool.to_schema()
            # Convert from Chat Completions format to Responses API format
            func = schema.get("function", {})
            schemas.append({
                "type": "function",
                "name": func.get("name"),
                "description": func.get("description"),
                "parameters": func.get("parameters"),
            })
        return schemas

    def execute(
        self,
        name: str,
        arguments: dict,
        *,
        interrupt_handler: InterruptHandler | None = None,
    ) -> str:
        """Execute a tool.

        Args:
            name: Tool name
            arguments: Tool arguments
            interrupt_handler: Optional interrupt handler for cancellation

        Returns:
            Tool execution result string.
        """
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: Unknown tool: {name}"
        return tool.execute(**arguments, _interrupt_handler=interrupt_handler)


def execute_tool(
    registry: ToolRegistry,
    name: str,
    arguments: dict,
    index: int,
    total: int,
    *,
    skip_permission: bool = False,
    interrupt_handler: InterruptHandler | None = None,
) -> str:
    """Execute a tool with permission check.

    Args:
        registry: Tool registry
        name: Tool name
        arguments: Tool arguments
        index: Current tool index
        total: Total number of tools
        skip_permission: Skip permission prompt
        interrupt_handler: Optional interrupt handler for cancellation

    Returns:
        Tool execution result string.

    Raises:
        InterruptRequested: If user requests interruption.
    """
    from lightcode.interrupt import InterruptRequested

    # Check for interrupt before permission prompt
    if interrupt_handler and interrupt_handler.is_interrupted():
        raise InterruptRequested()

    if not skip_permission:
        permission = request_permission(name, arguments, index, total)
        if permission is None:
            # User pressed Esc - signal interrupt
            if interrupt_handler:
                interrupt_handler.request_interrupt()
            raise InterruptRequested()
        if not permission:
            console.print("[muted]Tool execution denied[/]")
            return "Error: Tool execution was denied by user."
    else:
        # Skip mode: compact display
        console.print()
        header = render_tool_header(name, index, total)
        args_syntax = format_arguments(arguments)
        console.print(Panel(
            args_syntax,
            title=header,
            title_align="left",
            border_style="cyan",
        ))

    # Check for interrupt before execution
    if interrupt_handler and interrupt_handler.is_interrupted():
        raise InterruptRequested()

    try:
        with console.status(f"[bold cyan]Executing {name}...", spinner="dots"):
            result = registry.execute(name, arguments, interrupt_handler=interrupt_handler)
        is_error = False
    except InterruptRequested:
        raise
    except Exception as e:
        result = f"Error: {type(e).__name__}: {e}"
        is_error = True

    # Display result
    console.print(render_result(result, is_error))

    return result
