"""シンプルなREPLループ（LiteLLM対応・Tool Calling）"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import litellm
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme

from lightcode.tools import ALL_TOOLS, Tool, WebFetchTool, WebSearchTool

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
        result = registry.execute(name, arguments)
        is_error = False
    except Exception as e:
        result = f"Error: {type(e).__name__}: {e}"
        is_error = True

    # 結果を表示
    console.print(render_result(result, is_error))

    return result


def append_log(log_file: Path, entry: dict) -> None:
    """ログエントリをJSONLファイルに追記"""
    # 必要なフィールドだけを指定順序で出力
    field_order = ["timestamp", "role", "content", "tool_calls", "tool_call_id"]
    log_entry = {"timestamp": datetime.now().isoformat()}
    for field in field_order[1:]:  # timestamp以外
        if field in entry and entry[field] is not None:
            log_entry[field] = entry[field]
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def run_repl(
    *,
    skip_permission: bool = False,
    enable_web_search: bool = False,
    log_file: Path | None = None,
) -> None:
    """REPLを起動する"""
    console.print()
    console.print(Panel(
        "[bold]lightcode REPL[/] [dim](GPT-5.2 + Tool Calling)[/]",
        border_style="blue",
    ))
    if skip_permission:
        console.print("[warning]⚡ --no-permissions モード: ツール実行の許可確認をスキップ[/]")
    if enable_web_search:
        console.print("[success]🌐 Web検索が有効です (Tavily)[/]")
    if log_file:
        console.print(f"[success]📝 ログ出力: {log_file}[/]")
    console.print("[muted]終了するには 'exit' または 'quit' と入力してください[/]")
    console.print()

    # ツールリストを構築
    tools = list(ALL_TOOLS)
    if enable_web_search:
        tools.append(WebSearchTool())
        tools.append(WebFetchTool())

    model = "gpt-5.2"
    registry = ToolRegistry(tools)
    messages: list[dict] = []

    while True:
        try:
            user_input = input("> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            user_message = {"role": "user", "content": user_input}
            messages.append(user_message)
            if log_file:
                append_log(log_file, user_message)

            # LLMにリクエスト（ツール付き）
            while True:
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    tools=registry.get_schemas(),
                )

                choice = response.choices[0]
                assistant_message = choice.message

                # メッセージを履歴に追加
                assistant_dict = assistant_message.model_dump()
                messages.append(assistant_dict)
                if log_file:
                    append_log(log_file, assistant_dict)

                # ツール呼び出しがあるか確認
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

                        # ツール結果を追加
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                        messages.append(tool_message)
                        if log_file:
                            append_log(log_file, tool_message)
                    # ツール結果を渡して再度LLMを呼び出す
                    continue
                else:
                    # ツール呼び出しがなければ終了
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
    """エントリポイント"""
    parser = argparse.ArgumentParser(description="lightcode REPL")
    parser.add_argument(
        "--no-permissions",
        action="store_true",
        help="ツール実行時の許可確認をスキップする",
    )
    parser.add_argument(
        "--web-search",
        action="store_true",
        help="Web検索ツールを有効にする（TAVILY_API_KEY環境変数が必要）",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="LLMとのやり取りをJSONファイルに保存する",
    )
    args = parser.parse_args()

    run_repl(
        skip_permission=args.no_permissions,
        enable_web_search=args.web_search,
        log_file=args.log_file,
    )


if __name__ == "__main__":
    main()
