"""PowerPoint text search tool."""

import os
import re

from pptx import Presentation

from lightcode.tools.base import Tool


def _iter_shapes(shapes):
    for shape in shapes:
        yield shape
        if hasattr(shape, "shapes"):
            try:
                yield from _iter_shapes(shape.shapes)
            except Exception:
                pass


def _match_count(text: str, pattern: re.Pattern | None, query: str, case_sensitive: bool) -> int:
    if text is None:
        return 0
    if pattern:
        return len(pattern.findall(text))
    if case_sensitive:
        return text.count(query)
    return len(re.findall(re.escape(query), text, flags=re.IGNORECASE))


class PptxFindTextTool(Tool):
    """Tool for finding text across a PowerPoint deck."""

    @property
    def name(self) -> str:
        return "pptx_find_text"

    @property
    def description(self) -> str:
        return """Find text in a PowerPoint (.pptx) file across slides.

Searches text in shapes (including grouped shapes) and tables. Optionally includes speaker notes.
Regex search is supported."""

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the PowerPoint file (.pptx)",
                "required": True,
            },
            "query": {
                "type": "string",
                "description": "Text or regex pattern to find",
                "required": True,
            },
            "slide_numbers": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Slides to search (1-based). If omitted, searches all slides.",
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Case sensitive search (default: false)",
            },
            "use_regex": {
                "type": "boolean",
                "description": "Treat query as regex (default: false)",
            },
            "include_notes": {
                "type": "boolean",
                "description": "Include speaker notes in search (default: false)",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        query = kwargs.get("query")
        slide_numbers = kwargs.get("slide_numbers")
        case_sensitive = kwargs.get("case_sensitive", False)
        use_regex = kwargs.get("use_regex", False)
        include_notes = kwargs.get("include_notes", False)

        if not path:
            return "Error: path is required"
        if query is None:
            return "Error: query is required"
        if not os.path.exists(path):
            return f"Error: File not found: {path}"

        try:
            prs = Presentation(path)
            total_slides = len(prs.slides)
            if total_slides == 0:
                return f"PowerPoint file has no slides: {path}"

            if slide_numbers:
                slide_set = set(slide_numbers)
            else:
                slide_set = None

            pattern = None
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    pattern = re.compile(query, flags=flags)
                except re.error as e:
                    return f"Error: Invalid regex pattern: {e}"

            results = []
            total_matches = 0

            for idx, slide in enumerate(prs.slides, 1):
                if slide_set and idx not in slide_set:
                    continue

                # Shapes and tables
                for shape in _iter_shapes(slide.shapes):
                    if hasattr(shape, "text_frame"):
                        text = shape.text_frame.text
                        count = _match_count(text, pattern, query, case_sensitive)
                        if count > 0:
                            total_matches += count
                            snippet = text.replace("\n", " ")
                            if len(snippet) > 120:
                                snippet = snippet[:117] + "..."
                            results.append(
                                f"- Slide {idx} Shape {shape.shape_id}: {count} match(es) \"{snippet}\""
                            )

                    if getattr(shape, "has_table", False):
                        table = shape.table
                        for r, row in enumerate(table.rows, start=1):
                            for c, cell in enumerate(row.cells, start=1):
                                cell_text = cell.text_frame.text
                                count = _match_count(cell_text, pattern, query, case_sensitive)
                                if count > 0:
                                    total_matches += count
                                    snippet = cell_text.replace("\n", " ")
                                    if len(snippet) > 120:
                                        snippet = snippet[:117] + "..."
                                    results.append(
                                        f"- Slide {idx} Table Shape {shape.shape_id} Cell ({r},{c}): "
                                        f"{count} match(es) \"{snippet}\""
                                    )

                # Notes
                if include_notes and slide.has_notes_slide:
                    notes_text = slide.notes_slide.notes_text_frame.text
                    count = _match_count(notes_text, pattern, query, case_sensitive)
                    if count > 0:
                        total_matches += count
                        snippet = notes_text.replace("\n", " ")
                        if len(snippet) > 120:
                            snippet = snippet[:117] + "..."
                        results.append(
                            f"- Slide {idx} Notes: {count} match(es) \"{snippet}\""
                        )

            if not results:
                return "No matches found."

            header = f"Found {total_matches} match(es):"
            return "\n".join([header] + results)

        except Exception as e:
            return f"Error finding text: {e}"
