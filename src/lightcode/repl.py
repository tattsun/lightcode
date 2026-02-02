"""シンプルなREPLループ（LiteLLM対応・Tool Calling）"""

import json
import os

import litellm

# ツール定義
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "指定したディレクトリ内のファイルとフォルダの一覧を取得する",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "一覧を取得するディレクトリのパス（デフォルトはカレントディレクトリ）",
                    }
                },
                "required": [],
            },
        },
    }
]


def list_files(path: str = ".") -> str:
    """ディレクトリ内のファイル一覧を取得"""
    try:
        entries = os.listdir(path)
        result = []
        for entry in sorted(entries):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                result.append(f"[DIR]  {entry}")
            else:
                result.append(f"[FILE] {entry}")
        return "\n".join(result) if result else "(empty directory)"
    except FileNotFoundError:
        return f"Error: Directory not found: {path}"
    except PermissionError:
        return f"Error: Permission denied: {path}"


def request_permission(name: str, arguments: dict, index: int, total: int) -> bool:
    """ツール実行の許可をユーザーに求める"""
    print(f"\n[Tool Call Request ({index}/{total})]")
    print(f"  Name: {name}")
    print(f"  Args: {json.dumps(arguments, ensure_ascii=False)}")

    while True:
        answer = input("実行を許可しますか？ [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("y または n で回答してください")


def execute_tool(name: str, arguments: dict, index: int, total: int) -> str:
    """ツールを実行（許可を求める）"""
    if not request_permission(name, arguments, index, total):
        return "Error: Tool execution was denied by user."

    try:
        if name == "list_files":
            return list_files(arguments.get("path", "."))
        return f"Error: Unknown tool: {name}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def run_repl() -> None:
    """REPLを起動する"""
    print("lightcode REPL (GPT-5.2 + Tool Calling)")
    print("終了するには 'exit' または 'quit' と入力してください")
    print()

    messages: list[dict] = []

    while True:
        try:
            user_input = input("> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            messages.append({"role": "user", "content": user_input})

            # LLMにリクエスト（ツール付き）
            while True:
                response = litellm.completion(
                    model="gpt-5.2",
                    messages=messages,
                    tools=TOOLS,
                )

                choice = response.choices[0]
                assistant_message = choice.message

                # メッセージを履歴に追加
                messages.append(assistant_message.model_dump())

                # ツール呼び出しがあるか確認
                if assistant_message.tool_calls:
                    total = len(assistant_message.tool_calls)
                    for i, tool_call in enumerate(assistant_message.tool_calls, start=1):
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)

                        result = execute_tool(func_name, func_args, i, total)

                        # ツール結果を追加
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result,
                            }
                        )
                    # ツール結果を渡して再度LLMを呼び出す
                    continue
                else:
                    # ツール呼び出しがなければ終了
                    if assistant_message.content:
                        print(f"\n{assistant_message.content}\n")
                    break

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main() -> None:
    """エントリポイント"""
    run_repl()


if __name__ == "__main__":
    main()
