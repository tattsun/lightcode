"""File deletion tool."""

import os

from lightcode.tools.base import Tool


class DeleteFileTool(Tool):
    """Tool for deleting a file."""

    @property
    def name(self) -> str:
        return "delete_file"

    @property
    def description(self) -> str:
        return "Delete a file."

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file to delete",
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")

        if not path:
            return "Error: path is required"

        try:
            os.remove(path)
            return f"Deleted: {path}"
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except IsADirectoryError:
            return f"Error: Is a directory (use rmdir): {path}"
