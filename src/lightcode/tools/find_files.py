"""File name search tool."""

import fnmatch
import os

from lightcode.tools.base import Tool


class FindFilesTool(Tool):
    """Tool for searching files by name pattern."""

    @property
    def name(self) -> str:
        return "find_files"

    @property
    def description(self) -> str:
        return "Search for files by glob pattern."

    @property
    def parameters(self) -> dict:
        return {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to search for (e.g., *.py, test_*.py)",
                "required": True,
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current directory)",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (default: 100)",
            },
        }

    def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern")
        path = kwargs.get("path", ".")
        max_results = kwargs.get("max_results", 100)

        if not pattern:
            return "Error: pattern is required"

        results = []

        try:
            for root, dirs, files in os.walk(path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        filepath = os.path.join(root, filename)
                        results.append(filepath)
                        if len(results) >= max_results:
                            break

                if len(results) >= max_results:
                    break

        except FileNotFoundError:
            return f"Error: Path not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"

        if not results:
            return f"No files found matching '{pattern}'"

        output = "\n".join(results)
        if len(results) >= max_results:
            output += f"\n... (truncated at {max_results} results)"

        return output
