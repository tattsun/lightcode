"""File reading tool."""

from lightcode.tools.base import Tool


class ReadFileTool(Tool):
    """Tool for reading file contents."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file. Supports optional line range."

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file to read",
            },
            "start_line": {
                "type": "integer",
                "description": "Starting line number (1-based, optional)",
            },
            "end_line": {
                "type": "integer",
                "description": "Ending line number (inclusive, optional)",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        start_line = kwargs.get("start_line")
        end_line = kwargs.get("end_line")

        if not path:
            return "Error: path is required"

        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()

            total_lines = len(lines)

            # Normalize range (1-based to 0-based)
            start_idx = 0 if start_line is None else max(0, start_line - 1)
            end_idx = total_lines if end_line is None else min(total_lines, end_line)

            if start_idx >= total_lines:
                return f"Error: start_line ({start_line}) exceeds total lines ({total_lines})"

            selected_lines = lines[start_idx:end_idx]
            content = "".join(selected_lines)

            # Add metadata if range is specified
            if start_line is not None or end_line is not None:
                header = f"[Lines {start_idx + 1}-{start_idx + len(selected_lines)} of {total_lines}]\n"
                return header + content

            return content

        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except IsADirectoryError:
            return f"Error: Is a directory: {path}"
        except UnicodeDecodeError:
            return f"Error: Cannot decode file (binary?): {path}"
