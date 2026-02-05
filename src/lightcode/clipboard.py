"""Clipboard image grabbing utility."""

import base64
import io
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}


def _get_macos_clipboard_file_paths() -> list[str]:
    """Get file paths from macOS clipboard using osascript.

    Returns:
        List of POSIX file paths, or empty list if no files in clipboard
    """
    script = '''
    tell application "Finder"
        try
            set theItems to the clipboard as «class furl»
            return POSIX path of theItems
        on error
            try
                set theItems to the clipboard as alias
                return POSIX path of theItems
            on error
                return ""
            end try
        end try
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=2,
        )
        path = result.stdout.strip()
        if path:
            return [path]
    except Exception:
        pass
    return []


@dataclass
class ClipboardImage:
    """Image data from clipboard."""

    mime_type: str
    base64_data: str
    width: int
    height: int


def _load_image_from_path(path: str) -> "ClipboardImage | None":
    """Load image from file path.

    Args:
        path: Path to image file

    Returns:
        ClipboardImage or None if not a valid image
    """
    try:
        from PIL import Image
    except ImportError:
        return None

    file_path = Path(path)
    if not file_path.exists():
        return None

    # Check if it's an image file
    if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
        return None

    try:
        with Image.open(file_path) as img:
            # Convert to PNG bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            png_data = buffer.getvalue()

            # Encode to base64
            base64_data = base64.b64encode(png_data).decode("ascii")

            return ClipboardImage(
                mime_type="image/png",
                base64_data=base64_data,
                width=img.width,
                height=img.height,
            )
    except Exception:
        return None


def grab_clipboard_image() -> ClipboardImage | None:
    """Grab image from clipboard.

    Returns:
        ClipboardImage with base64 encoded PNG data, or None if:
        - No image in clipboard
        - Platform not supported (Linux)
        - PIL/ImageGrab not available
    """
    # Linux is not supported by ImageGrab
    if sys.platform == "linux":
        return None

    # On macOS, prefer file paths from clipboard to avoid Finder icon images
    if sys.platform == "darwin":
        file_paths = _get_macos_clipboard_file_paths()
        for path in file_paths:
            result = _load_image_from_path(path)
            if result:
                return result

    try:
        from PIL import ImageGrab
    except ImportError:
        return None

    try:
        image = ImageGrab.grabclipboard()
    except Exception:
        image = None

    if image is None:
        return None

    # ImageGrab can return a list of file paths (macOS/Windows file copy)
    if isinstance(image, list):
        # Try to load the first image file from the list
        for path in image:
            if isinstance(path, str):
                result = _load_image_from_path(path)
                if result:
                    return result
        return None

    # Check if it's a PIL Image object
    if not hasattr(image, "save"):
        return None

    # Convert to PNG bytes
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    png_data = buffer.getvalue()

    # Encode to base64
    base64_data = base64.b64encode(png_data).decode("ascii")

    return ClipboardImage(
        mime_type="image/png",
        base64_data=base64_data,
        width=image.width,
        height=image.height,
    )
