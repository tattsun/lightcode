"""Image reading tool for multimodal LLM support."""

import base64
import mimetypes
from pathlib import Path

from lightcode.tools.base import Tool

# Supported image formats
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class ReadImageTool(Tool):
    """Tool for reading image files and returning base64 encoded data."""

    @property
    def name(self) -> str:
        return "read_image"

    @property
    def description(self) -> str:
        return (
            "Read an image file and return it for visual recognition by the LLM. "
            "Supported formats: PNG, JPEG, GIF, WebP."
        )

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the image file",
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path")

        if not path_str:
            return "Error: path is required"

        path = Path(path_str)

        # Check file exists
        if not path.exists():
            return f"Error: File not found: {path}"

        if not path.is_file():
            return f"Error: Not a file: {path}"

        # Check file extension
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_FORMATS:
            return (
                f"Error: Unsupported image format: {suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            # Fallback based on extension
            mime_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_map.get(suffix, "application/octet-stream")

        try:
            # Read and encode image
            image_data = path.read_bytes()
            base64_data = base64.b64encode(image_data).decode("utf-8")

            # Return special format for REPL to parse
            # Format: [IMAGE:mime_type:base64_data]
            return f"[IMAGE:{mime_type}:{base64_data}]"

        except PermissionError:
            return f"Error: Permission denied: {path}"
        except OSError as e:
            return f"Error: Failed to read file: {e}"
