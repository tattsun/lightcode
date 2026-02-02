"""File copy tool."""

import shutil

from lightcode.tools.base import Tool


class CopyFileTool(Tool):
    """Tool for copying a file."""

    @property
    def name(self) -> str:
        return "copy_file"

    @property
    def description(self) -> str:
        return "Copy a file."

    @property
    def parameters(self) -> dict:
        return {
            "source": {
                "type": "string",
                "description": "Source file path",
                "required": True,
            },
            "destination": {
                "type": "string",
                "description": "Destination path",
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        source = kwargs.get("source")
        destination = kwargs.get("destination")

        if not source:
            return "Error: source is required"
        if not destination:
            return "Error: destination is required"

        try:
            shutil.copy2(source, destination)
            return f"Copied: {source} -> {destination}"
        except FileNotFoundError:
            return f"Error: File not found: {source}"
        except PermissionError:
            return f"Error: Permission denied"
        except IsADirectoryError:
            return f"Error: Destination is a directory: {destination}"
        except shutil.SameFileError:
            return f"Error: Source and destination are the same file"
