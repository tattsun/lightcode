"""ツールの登録・管理"""

from rich.panel import Panel

from lightcode.tools import Tool
from lightcode.ui import (
    console,
    format_arguments,
    render_result,
    render_tool_header,
    request_permission,
)


class ToolRegistry:
    """ツールの登録・管理"""

    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def get_schemas(self) -> list[dict]:
        """全ツールのスキーマを取得"""
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict) -> str:
        """ツールを実行"""
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: Unknown tool: {name}"
        return tool.execute(**arguments)


def execute_tool(
    registry: ToolRegistry,
    name: str,
    arguments: dict,
    index: int,
    total: int,
    *,
    skip_permission: bool = False,
) -> str:
    """ツールを実行（許可を求める）"""
    if not skip_permission:
        if not request_permission(name, arguments, index, total):
            console.print("[muted]Tool execution denied[/]")
            return "Error: Tool execution was denied by user."
    else:
        # スキップモード: コンパクトな表示
        console.print()
        header = render_tool_header(name, index, total)
        args_syntax = format_arguments(arguments)
        console.print(Panel(
            args_syntax,
            title=header,
            title_align="left",
            border_style="cyan",
        ))

    try:
        with console.status(f"[bold cyan]Executing {name}...", spinner="dots"):
            result = registry.execute(name, arguments)
        is_error = False
    except Exception as e:
        result = f"Error: {type(e).__name__}: {e}"
        is_error = True

    # 結果を表示
    console.print(render_result(result, is_error))

    return result
