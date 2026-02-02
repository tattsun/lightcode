"""Shell command execution tool."""

import subprocess

from lightcode.tools.base import Tool


class RunCommandTool(Tool):
    """Tool for executing shell commands."""

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return "Execute a shell command. Use for builds, tests, git operations, etc."

    @property
    def parameters(self) -> dict:
        return {
            "command": {
                "type": "string",
                "description": "Shell command to execute",
                "required": True,
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 60)",
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
