"""Shell command execution tool."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from lightcode.tools.base import Tool

if TYPE_CHECKING:
    from lightcode.interrupt import InterruptHandler


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
        from lightcode.interrupt import InterruptRequested

        command = kwargs.get("command")
        timeout = kwargs.get("timeout", 60)
        interrupt_handler: InterruptHandler | None = kwargs.get("_interrupt_handler")

        if not command:
            return "Error: command is required"

        try:
            # Start subprocess in new session to prevent SIGINT propagation
            popen_kwargs: dict = {
                "shell": True,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
            }
            if sys.platform != "win32":
                popen_kwargs["start_new_session"] = True
            else:
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            process = subprocess.Popen(command, **popen_kwargs)

            start_time = time.time()
            poll_interval = 0.1  # 100ms

            while True:
                # Check for interrupt
                if interrupt_handler and interrupt_handler.is_interrupted():
                    process.terminate()
                    try:
                        process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    raise InterruptRequested()

                # Check for process completion
                returncode = process.poll()
                if returncode is not None:
                    break

                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    process.kill()
                    process.wait()
                    return f"Error: Command timed out after {timeout} seconds"

                time.sleep(poll_interval)

            stdout, stderr = process.communicate()

            output = ""
            if stdout:
                output += stdout
            if stderr:
                if output:
                    output += "\n"
                output += f"[stderr]\n{stderr}"

            if process.returncode != 0:
                output += f"\n[exit code: {process.returncode}]"

            return output if output else "(no output)"

        except InterruptRequested:
            raise
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"
