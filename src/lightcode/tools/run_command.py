"""シェルコマンド実行ツール"""

import subprocess

from lightcode.tools.base import Tool


class RunCommandTool(Tool):
    """シェルコマンドを実行するツール"""

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return "シェルコマンドを実行する。ビルド、テスト、git操作などに使用。"

    @property
    def parameters(self) -> dict:
        return {
            "command": {
                "type": "string",
                "description": "実行するシェルコマンド",
                "required": True,
            },
            "timeout": {
                "type": "integer",
                "description": "タイムアウト秒数（デフォルト: 60）",
            },
        }

    def execute(self, **kwargs) -> str:
        command = kwargs.get("command")
        timeout = kwargs.get("timeout", 60)

        if not command:
            return "Error: command is required"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                if output:
                    output += "\n"
                output += f"[stderr]\n{result.stderr}"

            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"

            return output if output else "(no output)"

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"
