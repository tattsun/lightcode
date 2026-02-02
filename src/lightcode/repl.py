"""シンプルなREPLループ（LiteLLM対応・Tool Calling）"""

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


def run_repl(
    *,
    skip_permission: bool = False,
    enable_web_search: bool = False,
    log_file: Path | None = None,
) -> None:
    """REPLを起動する"""
    model = os.environ.get("LIGHTCODE_MODEL", "gpt-5.2")

    console.print()
    console.print(Panel(
        f"[bold]lightcode REPL[/] [dim]({model} + Tool Calling)[/]",
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
    model_info = litellm.get_model_info(model)
    max_tokens = model_info.get("max_input_tokens", 128_000)
    registry = ToolRegistry(tools)
    messages: list[dict] = []

    def format_tokens(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K"
        return str(n)

    while True:
        try:
            # ステータス行を表示
            token_count = litellm.token_counter(model=model, messages=messages)
            percentage = token_count * 100 // max_tokens
            console.print(f"[muted]{token_count:,} / {format_tokens(max_tokens)} tokens ({percentage} %)[/]")

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
