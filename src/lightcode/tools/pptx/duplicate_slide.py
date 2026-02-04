"""PowerPoint slide duplication tool."""

import os
from copy import deepcopy

from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

from lightcode.tools.base import Tool


def _copy_slide_shapes(source_slide, target_slide):
    """Copy all shapes from source to target slide (including groups)."""
    # Remove existing shapes from target (leave required group properties)
    for shape in list(target_slide.shapes):
        sp = shape._element
        target_slide.shapes._spTree.remove(sp)

    # Insert shapes in original order to preserve z-order
    for shape in source_slide.shapes:
        target_slide.shapes._spTree.insert_element_before(
            deepcopy(shape._element),
            "p:extLst",
        )


def _copy_slide_background(source_slide, target_slide):
    """Copy background settings if available."""
    try:
        src_bg = source_slide._element.cSld.bg
        if src_bg is not None:
            target_slide._element.cSld.bg = deepcopy(src_bg)
    except Exception:
        # Background copying is best-effort
        return


def _copy_relationships(source_slide, target_slide):
    """Copy relationships needed by shapes (images, hyperlinks, media, etc.)."""
    for rel in source_slide.part.rels:
        # Skip layout relationship (already present) and notes
        if rel.reltype in (RT.SLIDE_LAYOUT, RT.NOTES_SLIDE):
            continue

        # If rId already exists in target, skip to avoid collision
        if rel.rId in target_slide.part.rels:
            continue

        if rel.is_external:
            target_slide.part.rels.add_relationship(
                rel.reltype,
                rel.target_ref,
                rel.rId,
                is_external=True,
            )
        else:
            target_slide.part.rels.add_relationship(
                rel.reltype,
                rel._target,
                rel.rId,
            )


class PptxDuplicateSlideTool(Tool):
    """Tool for duplicating slides in PowerPoint presentations."""

    @property
    def name(self) -> str:
        return "pptx_duplicate_slide"

    @property
    def description(self) -> str:
        return """Duplicate an existing slide in a PowerPoint (.pptx) file.

The duplicated slide preserves:
- Layout
- Shapes and z-order
- Background (best-effort)
- Relationships for images/hyperlinks (best-effort)

Notes are copied as plain text."""

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Path to the PowerPoint file (.pptx)",
                "required": True,
            },
            "source_slide": {
                "type": "integer",
                "description": "Slide number to duplicate (1-based)",
                "required": True,
            },
            "position": {
                "type": "integer",
                "description": "Position to insert duplicated slide (1-based). If omitted, adds at the end.",
            },
            "copy_notes": {
                "type": "boolean",
                "description": "Copy speaker notes text (default: true)",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        source_slide_num = kwargs.get("source_slide")
        position = kwargs.get("position")
        copy_notes = kwargs.get("copy_notes", True)

        if not path:
            return "Error: path is required"
        if source_slide_num is None:
            return "Error: source_slide is required"
        if not os.path.exists(path):
            return f"Error: File not found: {path}"

        try:
            prs = Presentation(path)
            total_slides = len(prs.slides)

            if source_slide_num < 1 or source_slide_num > total_slides:
                return f"Error: Invalid slide number {source_slide_num}. File has {total_slides} slide(s)."

            source_slide = prs.slides[source_slide_num - 1]

            # Create new slide with same layout
            new_slide = prs.slides.add_slide(source_slide.slide_layout)

            _copy_slide_shapes(source_slide, new_slide)
            _copy_slide_background(source_slide, new_slide)
            _copy_relationships(source_slide, new_slide)

            # Copy notes text (best-effort)
            if copy_notes and source_slide.has_notes_slide:
                notes_text = source_slide.notes_slide.notes_text_frame.text
                if notes_text:
                    new_slide.notes_slide.notes_text_frame.text = notes_text

            # Move slide to specified position if needed
            new_slide_idx = len(prs.slides) - 1
            if position is not None:
                target_idx = max(0, min(position - 1, len(prs.slides) - 1))
                if target_idx != new_slide_idx:
                    slides = prs.slides._sldIdLst
                    slide_id = slides[-1]
                    slides.remove(slide_id)
                    slides.insert(target_idx, slide_id)
                    new_slide_idx = target_idx

            prs.save(path)

            slide_position = new_slide_idx + 1
            return (
                f"Successfully duplicated slide {source_slide_num} "
                f"to position {slide_position}. Total slides: {len(prs.slides)}"
            )

        except Exception as e:
            return f"Error duplicating slide: {e}"
