"""File writing tool."""

import os

from lightcode.tools.base import Tool


class WriteFileTool(Tool):
    """Tool for writing content to a file."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file (overwrites existing file)"

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        content = kwargs.get("content")

        if not path:
            return "Error: path is required"
        if content is None:
            return "Error: content is required"

        try:
            # Create parent directory if it doesn't exist
            parent = os.path.dirname(path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"Successfully wrote {len(content)} bytes to {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except IsADirectoryError:
            return f"Error: Is a directory: {path}"
