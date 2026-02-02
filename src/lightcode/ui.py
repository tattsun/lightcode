"""UI表示関連の機能"""

import json

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme

# カスタムテーマ
custom_theme = Theme({
    "tool.name": "bold cyan",
    "tool.index": "dim",
    "success": "green",
    "error": "bold red",
    "warning": "yellow",
    "muted": "dim",
})

console = Console(theme=custom_theme)

# 表示制限
MAX_RESULT_LINES = 5
MAX_LINE_LENGTH = 80


def truncate_result(result: str) -> str:
    """ツールの結果を省略して表示用に整形"""
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
    """引数をJSON構文ハイライト付きで整形"""
    json_str = json.dumps(arguments, ensure_ascii=False, indent=2)
    return Syntax(json_str, "json", theme="monokai", line_numbers=False)


def render_tool_header(name: str, index: int, total: int) -> Text:
    """ツールヘッダーをリッチテキストで生成"""
    text = Text()
    text.append("🔧 ", style="bold")
    text.append(name, style="tool.name")
    text.append(f"  ({index}/{total})", style="tool.index")
    return text


def render_result(result: str, is_error: bool = False) -> Panel:
    """ツール結果をパネルで表示"""
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


def request_permission(name: str, arguments: dict, index: int, total: int) -> bool:
    """ツール実行の許可をユーザーに求める"""
    console.print()

    # ヘッダー
    header = render_tool_header(name, index, total)

    # 引数パネル
    args_syntax = format_arguments(arguments)

    # パネルで表示
    console.print(Panel(
        args_syntax,
        title=header,
        title_align="left",
        border_style="yellow",
        subtitle="⚠️  Permission Required",
        subtitle_align="right",
    ))

    while True:
        answer = console.input("[yellow]実行を許可しますか？ [y/n]:[/] ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        console.print("[warning]y または n で回答してください[/]")
