"""File editing tool (search and replace)."""

from lightcode.tools.base import Tool


class EditFileTool(Tool):
    """Tool for searching and replacing text in a file."""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Search for a string in a file and replace it. The old_string must be unique."

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the file to edit",
            },
            "old_string": {
                "type": "string",
                "description": "String to search for (must match uniquely)",
            },
            "new_string": {
                "type": "string",
                "description": "Replacement string",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")

        if not path:
            return "Error: path is required"
        if old_string is None:
            return "Error: old_string is required"
        if new_string is None:
            return "Error: new_string is required"

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Count matches
            count = content.count(old_string)

            if count == 0:
                return f"Error: old_string not found in {path}"
            if count > 1:
                return f"Error: old_string matches {count} times. Please provide more context to make it unique."

            # Perform replacement
            new_content = content.replace(old_string, new_string, 1)

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Change statistics
            old_lines = old_string.count("\n") + 1
            new_lines = new_string.count("\n") + 1
            return f"Successfully edited {path}: replaced {old_lines} lines with {new_lines} lines"

        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except IsADirectoryError:
            return f"Error: Is a directory: {path}"
        except UnicodeDecodeError:
            return f"Error: Cannot decode file (binary?): {path}"
