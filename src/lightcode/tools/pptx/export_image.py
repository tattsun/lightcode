"""PowerPoint slide image export tool."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from pdf2image import convert_from_path

from lightcode.tools.base import Tool


def check_libreoffice() -> str | None:
    """Check if LibreOffice is available.

    Returns:
        Path to soffice command if found, None otherwise.
    """
    # Check common paths
    paths_to_check = [
        "soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]

    for path in paths_to_check:
        if shutil.which(path):
            return path

    return None


def check_poppler() -> bool:
    """Check if Poppler (pdftoppm) is available."""
    return shutil.which("pdftoppm") is not None


class PptxExportImageTool(Tool):
    """Tool for exporting PowerPoint slides as PNG images."""

    @property
    def name(self) -> str:
        return "pptx_export_image"

    @property
    def description(self) -> str:
        return (
            "Export PowerPoint slides as PNG images for visual verification. "
            "When checking exported images, verify: "
            "1. No text overflow/clipping outside shape boundaries "
            "2. Consistent font sizes across shapes "
            "3. Proper alignment and layout. "
            "If issues are found, fix them and re-export until resolved. "
            "Output files are saved to /tmp by default. "
            "Requires LibreOffice and Poppler to be installed. "
            "On macOS: brew install libreoffice poppler"
        )

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the PowerPoint file (.pptx)",
                "required": True,
            },
            "slide_number": {
                "type": "integer",
                "description": "Export only this slide (1-based). If omitted, all slides are exported.",
            },
            "output": {
                "type": "string",
                "description": "Output file path (e.g., /tmp/slide.png). For multiple slides, _1, _2 suffixes are added. Default: /tmp/slide_{n}.png",
            },
            "dpi": {
                "type": "integer",
                "description": "Resolution in DPI (default: 150)",
            },
        }

    def execute(self, **kwargs) -> str:
        path_str = kwargs.get("path")
        slide_number = kwargs.get("slide_number")
        output_str = kwargs.get("output")
        dpi = kwargs.get("dpi", 150)

        if not path_str:
            return "Error: path is required"

        pptx_path = Path(path_str)

        # Validate file
        if not pptx_path.exists():
            return f"Error: File not found: {pptx_path}"

        if not pptx_path.is_file():
            return f"Error: Not a file: {pptx_path}"

        if pptx_path.suffix.lower() not in (".pptx", ".ppt"):
            return f"Error: Not a PowerPoint file: {pptx_path}"

        # Check dependencies
        soffice_path = check_libreoffice()
        if not soffice_path:
            return (
                "Error: LibreOffice not found. "
                "Please install it:\n"
                "  macOS: brew install --cask libreoffice\n"
                "  Ubuntu: sudo apt install libreoffice"
            )

        if not check_poppler():
            return (
                "Error: Poppler not found (pdftoppm command). "
                "Please install it:\n"
                "  macOS: brew install poppler\n"
                "  Ubuntu: sudo apt install poppler-utils"
            )

        try:
            # Step 1: Convert PPTX to PDF using LibreOffice
            with tempfile.TemporaryDirectory() as pdf_temp_dir:
                result = subprocess.run(
                    [
                        soffice_path,
                        "--headless",
                        "--convert-to", "pdf",
                        "--outdir", pdf_temp_dir,
                        str(pptx_path.absolute()),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode != 0:
                    return f"Error: LibreOffice conversion failed:\n{result.stderr}"

                # Find the generated PDF
                pdf_files = list(Path(pdf_temp_dir).glob("*.pdf"))
                if not pdf_files:
                    return "Error: LibreOffice did not generate a PDF file"

                pdf_path = pdf_files[0]

                # Step 2: Convert PDF to PNG images using pdf2image
                images = convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    fmt="png",
                )

                # Save images
                exported_paths = []

                if slide_number is not None:
                    # Export only the specified slide
                    if slide_number < 1 or slide_number > len(images):
                        return (
                            f"Error: slide_number {slide_number} is out of range. "
                            f"Presentation has {len(images)} slides."
                        )

                    image = images[slide_number - 1]
                    # Determine output path
                    if output_str:
                        output_path = Path(output_str)
                    else:
                        output_path = Path(f"/tmp/slide_{slide_number}.png")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(str(output_path), "PNG")
                    exported_paths.append(str(output_path))
                else:
                    # Export all slides
                    for i, image in enumerate(images, start=1):
                        if output_str:
                            # Add suffix before extension: foo.png -> foo_1.png
                            base_path = Path(output_str)
                            output_path = base_path.parent / f"{base_path.stem}_{i}{base_path.suffix}"
                        else:
                            output_path = Path(f"/tmp/slide_{i}.png")
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        image.save(str(output_path), "PNG")
                        exported_paths.append(str(output_path))

            # Return the list of exported files
            if len(exported_paths) == 1:
                return f"Exported 1 slide:\n{exported_paths[0]}"
            else:
                files_list = "\n".join(exported_paths)
                return f"Exported {len(exported_paths)} slides:\n{files_list}"

        except subprocess.TimeoutExpired:
            return "Error: LibreOffice conversion timed out"
        except Exception as e:
            return f"Error: Export failed: {e}"
