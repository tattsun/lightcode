"""File info tool."""

import os
from datetime import datetime

from lightcode.tools.base import Tool


class FileInfoTool(Tool):
    """Tool for getting file information."""

    @property
    def name(self) -> str:
        return "file_info"

    @property
    def description(self) -> str:
        return "Get file size, modification time, permissions, etc."

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file",
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")

        if not path:
            return "Error: path is required"

        try:
            stat = os.stat(path)

            # File type
            if os.path.isfile(path):
                file_type = "file"
            elif os.path.isdir(path):
                file_type = "directory"
            elif os.path.islink(path):
                file_type = "symlink"
            else:
                file_type = "other"

            # Format size
            size = stat.st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            # Format timestamps
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            ctime = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")

            # Permissions
            mode = oct(stat.st_mode)[-3:]

            info = f"""Path: {path}
Type: {file_type}
Size: {size_str} ({size} bytes)
Modified: {mtime}
Created: {ctime}
Permissions: {mode}"""

            return info

        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
