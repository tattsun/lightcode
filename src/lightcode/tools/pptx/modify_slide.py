"""PowerPoint slide modification tool."""

import os
import json
from pptx import Presentation

from lightcode.tools.base import Tool
from pptx.util import Pt, Inches

from lightcode.tools.pptx._common import add_shape, hex_to_rgb


class PptxModifySlideTool(Tool):
    """Tool for modifying slides in PowerPoint presentations."""

    @property
    def name(self) -> str:
        return "pptx_modify_slide"

    @property
    def description(self) -> str:
        return """Modify an existing slide in a PowerPoint (.pptx) file. USE THIS TOOL instead of writing Python code to edit PowerPoint files.

IMPORTANT: After modifying a slide, ALWAYS use pptx_export_image + read_image to visually verify the changes look correct.

Actions:
- Update existing shapes by ID (change text, font_size, colors) via update_shapes
- Add new shapes via add_shapes
- Remove shapes by ID via remove_shape_ids
- Delete the entire slide via delete

First use pptx_read to get shape IDs and positions.

update_shapes examples:
- Change text: [{"shape_id": 2, "text": "New text"}]
- Rich text (partial bold/styles): [{"shape_id": 2, "rich_text": [{"text": "Normal "}, {"text": "BOLD", "bold": true}, {"text": " normal"}]}]
- Rich text with colors: [{"shape_id": 2, "rich_text": [{"text": "Black "}, {"text": "Red", "font_color": "#FF0000"}]}]
- Change font size only (no text change): [{"shape_id": 2, "font_size": 24}]
- Change font: [{"shape_id": 2, "font_name": "Arial"}]
- Change text and style: [{"shape_id": 2, "text": "New", "font_size": 18, "font_color": "#FF0000", "bold": true}]
- Change fill color: [{"shape_id": 2, "fill_color": "#0000FF"}]
- Change position: [{"shape_id": 2, "left": 1.0, "top": 2.0}]
- Change size: [{"shape_id": 2, "width": 4.0, "height": 2.0}]

rich_text segment properties: text (required), bold, italic, underline, font_size, font_name, font_color, font_theme_color, hyperlink
font_theme_color values: TEXT_1, TEXT_2, ACCENT_1-6, BACKGROUND_1-2, DARK_1-2, LIGHT_1-2
hyperlink example: {"text": "Click here", "hyperlink": "https://example.com"}
If a property is not specified in a segment, the original shape's style is preserved.

add_shapes example:
[{"type": "textbox", "left": 1.0, "top": 5.0, "width": 4.0, "height": 1.0, "text": "Text", "font_size": 18}]

Shape types: textbox, rectangle, rounded_rectangle, oval, arrow_right, arrow_left, etc.
Coordinates in inches. Use pptx_read to get actual slide dimensions."""

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
                "description": "Slide number to modify (1-based, starts from 1 NOT 0)",
                "required": True,
            },
            "update_shapes": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Update existing shapes by ID. Each: {shape_id, text, rich_text, font_size, font_name, font_color, bold, italic, underline, fill_color, left, top, width, height}. Use rich_text for partial styling: [{text, bold, italic, underline, font_size, font_name, font_color}, ...]",
            },
            "add_shapes": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Add new shapes. Each: {type, left, top, width, height, text, fill_color, font_size, font_name, font_color, bold, alignment}",
            },
            "remove_shape_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Array of shape IDs to remove (get IDs from pptx_read)",
            },
            "notes": {
                "type": "string",
                "description": "New speaker notes",
            },
            "delete": {
                "type": "boolean",
                "description": "Delete this slide entirely",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        slide_number = kwargs.get("slide_number")
        update_shapes = kwargs.get("update_shapes", [])
        add_shapes_list = kwargs.get("add_shapes", [])
        remove_shape_ids = kwargs.get("remove_shape_ids", [])
        notes = kwargs.get("notes")
        delete = kwargs.get("delete", False)

        if not path:
            return "Error: path is required"
        if slide_number is None:
            return "Error: slide_number is required"

        if not os.path.exists(path):
            return f"Error: File not found: {path}"

        try:
            prs = Presentation(path)
            total_slides = len(prs.slides)

            if slide_number < 1:
                return f"Error: slide_number must be >= 1 (1-based indexing). You passed {slide_number}. Use slide_number=1 for the first slide."
            if slide_number > total_slides:
                return f"Error: slide_number {slide_number} is out of range. File has {total_slides} slide(s). Valid range: 1-{total_slides}."

            slide_idx = slide_number - 1

            # Handle slide deletion
            if delete:
                slide_id = prs.slides._sldIdLst[slide_idx]
                prs.part.drop_rel(slide_id.rId)
                prs.slides._sldIdLst.remove(slide_id)
                prs.save(path)
                return f"Successfully deleted slide {slide_number}. Remaining slides: {len(prs.slides)}"

            slide = prs.slides[slide_idx]
            modifications = []

            # Parse JSON strings
            if isinstance(update_shapes, str):
                try:
                    update_shapes = json.loads(update_shapes)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in update_shapes: {e}"

            if isinstance(add_shapes_list, str):
                try:
                    add_shapes_list = json.loads(add_shapes_list)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in add_shapes: {e}"

            if isinstance(remove_shape_ids, str):
                try:
                    remove_shape_ids = json.loads(remove_shape_ids)
                except json.JSONDecodeError:
                    remove_shape_ids = [int(remove_shape_ids)]

            # Update existing shapes by ID
            if update_shapes:
                updated_count = 0
                not_found_ids = []

                # Build shape map including shapes inside groups (recursive)
                def collect_shapes(shapes):
                    result = {}
                    for shape in shapes:
                        result[shape.shape_id] = shape
                        # Recursively collect shapes from groups
                        if hasattr(shape, "shapes"):
                            result.update(collect_shapes(shape.shapes))
                    return result

                shape_map = collect_shapes(slide.shapes)

                for update_data in update_shapes:
                    if isinstance(update_data, str):
                        try:
                            update_data = json.loads(update_data)
                        except json.JSONDecodeError:
                            continue

                    shape_id = update_data.get("shape_id")
                    if shape_id is None:
                        continue

                    shape = shape_map.get(shape_id)
                    if shape is None:
                        not_found_ids.append(shape_id)
                        continue

                    # Update text content (preserving existing styles)
                    has_text_update = "text" in update_data or "rich_text" in update_data
                    if has_text_update and hasattr(shape, "text_frame"):
                        tf = shape.text_frame

                        # Save existing font styles from first run/paragraph
                        saved_font_size = None
                        saved_font_color_rgb = None
                        saved_font_color_theme = None
                        saved_font_color_brightness = None
                        saved_font_bold = None
                        saved_font_italic = None
                        saved_font_underline = None
                        saved_font_name = None

                        if tf.paragraphs:
                            first_para = tf.paragraphs[0]
                            if first_para.runs:
                                first_run = first_para.runs[0]
                                saved_font_size = first_run.font.size
                                saved_font_bold = first_run.font.bold
                                saved_font_italic = first_run.font.italic
                                saved_font_underline = first_run.font.underline
                                saved_font_name = first_run.font.name
                                if first_run.font.color and first_run.font.color.type is not None:
                                    try:
                                        saved_font_color_rgb = first_run.font.color.rgb
                                    except (AttributeError, TypeError):
                                        pass
                                    try:
                                        saved_font_color_theme = first_run.font.color.theme_color
                                        saved_font_color_brightness = first_run.font.color.brightness
                                    except (AttributeError, TypeError):
                                        pass
                            else:
                                saved_font_size = first_para.font.size
                                saved_font_bold = first_para.font.bold
                                saved_font_italic = first_para.font.italic
                                saved_font_underline = first_para.font.underline
                                saved_font_name = first_para.font.name
                                if first_para.font.color and first_para.font.color.type is not None:
                                    try:
                                        saved_font_color_rgb = first_para.font.color.rgb
                                    except (AttributeError, TypeError):
                                        pass
                                    try:
                                        saved_font_color_theme = first_para.font.color.theme_color
                                        saved_font_color_brightness = first_para.font.color.brightness
                                    except (AttributeError, TypeError):
                                        pass

                        # Clear existing text
                        for para in tf.paragraphs:
                            para.clear()

                        # Helper to apply saved styles to a run
                        def apply_base_styles(run, segment=None):
                            """Apply saved base styles to a run, with optional segment overrides."""
                            seg = segment or {}
                            # Font size
                            if "font_size" in seg:
                                run.font.size = Pt(seg["font_size"])
                            elif saved_font_size:
                                run.font.size = saved_font_size
                            # Font name
                            if "font_name" in seg:
                                run.font.name = seg["font_name"]
                            elif saved_font_name:
                                run.font.name = saved_font_name
                            # Bold
                            if "bold" in seg:
                                run.font.bold = seg["bold"]
                            elif saved_font_bold is not None:
                                run.font.bold = saved_font_bold
                            # Italic
                            if "italic" in seg:
                                run.font.italic = seg["italic"]
                            elif saved_font_italic is not None:
                                run.font.italic = saved_font_italic
                            # Underline
                            if "underline" in seg:
                                run.font.underline = seg["underline"]
                            elif saved_font_underline is not None:
                                run.font.underline = saved_font_underline
                            # Color
                            if "font_color" in seg:
                                run.font.color.rgb = hex_to_rgb(seg["font_color"])
                            elif saved_font_color_rgb:
                                run.font.color.rgb = saved_font_color_rgb
                            elif saved_font_color_theme is not None:
                                run.font.color.theme_color = saved_font_color_theme
                                if saved_font_color_brightness is not None:
                                    run.font.color.brightness = saved_font_color_brightness

                        if "rich_text" in update_data:
                            # Rich text: multiple runs with individual styles
                            rich_text = update_data["rich_text"]
                            if isinstance(rich_text, str):
                                rich_text = json.loads(rich_text)

                            first_para = tf.paragraphs[0]
                            for i, segment in enumerate(rich_text):
                                if isinstance(segment, str):
                                    segment = json.loads(segment)
                                text = segment.get("text", "")
                                if i == 0:
                                    # First segment: set paragraph text (creates first run)
                                    first_para.text = text
                                    if first_para.runs:
                                        apply_base_styles(first_para.runs[0], segment)
                                else:
                                    # Subsequent segments: add new run
                                    run = first_para.add_run()
                                    run.text = text
                                    apply_base_styles(run, segment)
                        else:
                            # Simple text update
                            tf.paragraphs[0].text = update_data["text"]

                            # Re-apply saved styles (unless overridden by update_data)
                            first_para = tf.paragraphs[0]
                            if first_para.runs:
                                apply_base_styles(first_para.runs[0], update_data)

                    # Update font styling (works with or without text change)
                    has_font_update = any(
                        k in update_data for k in ["font_size", "font_color", "bold", "italic", "underline", "font_name"]
                    )
                    if has_font_update and hasattr(shape, "text_frame"):
                        tf = shape.text_frame
                        for para in tf.paragraphs:
                            for run in para.runs:
                                if "font_size" in update_data:
                                    run.font.size = Pt(update_data["font_size"])
                                if "font_color" in update_data:
                                    run.font.color.rgb = hex_to_rgb(update_data["font_color"])
                                if "bold" in update_data:
                                    run.font.bold = update_data["bold"]
                                if "italic" in update_data:
                                    run.font.italic = update_data["italic"]
                                if "underline" in update_data:
                                    run.font.underline = update_data["underline"]
                                if "font_name" in update_data:
                                    run.font.name = update_data["font_name"]
                            # Also update paragraph-level font if no runs
                            if not para.runs:
                                if "font_size" in update_data:
                                    para.font.size = Pt(update_data["font_size"])
                                if "font_color" in update_data:
                                    para.font.color.rgb = hex_to_rgb(update_data["font_color"])
                                if "bold" in update_data:
                                    para.font.bold = update_data["bold"]
                                if "italic" in update_data:
                                    para.font.italic = update_data["italic"]
                                if "underline" in update_data:
                                    para.font.underline = update_data["underline"]
                                if "font_name" in update_data:
                                    para.font.name = update_data["font_name"]

                    # Update fill color
                    if "fill_color" in update_data and hasattr(shape, "fill"):
                        shape.fill.solid()
                        shape.fill.fore_color.rgb = hex_to_rgb(update_data["fill_color"])

                    # Update position and size
                    if "left" in update_data:
                        shape.left = Inches(float(update_data["left"]))
                    if "top" in update_data:
                        shape.top = Inches(float(update_data["top"]))
                    if "width" in update_data:
                        shape.width = Inches(float(update_data["width"]))
                    if "height" in update_data:
                        shape.height = Inches(float(update_data["height"]))

                    updated_count += 1

                if updated_count > 0:
                    modifications.append(f"{updated_count} shape(s) updated")
                if not_found_ids:
                    modifications.append(f"shape_id not found: {not_found_ids}")

            # Remove shapes by ID
            if remove_shape_ids:
                removed_count = 0
                sp_tree = slide.shapes._spTree

                for shape in list(slide.shapes):
                    if shape.shape_id in remove_shape_ids:
                        sp = shape._element
                        sp_tree.remove(sp)
                        removed_count += 1

                if removed_count > 0:
                    modifications.append(f"{removed_count} shape(s) removed")

            # Add new shapes
            if add_shapes_list:
                added_count = 0
                for shape_data in add_shapes_list:
                    if isinstance(shape_data, str):
                        try:
                            shape_data = json.loads(shape_data)
                        except json.JSONDecodeError:
                            continue

                    shape_type = shape_data.get("type", "textbox")
                    left = float(shape_data.get("left", 0))
                    top = float(shape_data.get("top", 0))
                    width = float(shape_data.get("width", 2))
                    height = float(shape_data.get("height", 1))

                    add_shape(
                        slide,
                        shape_type=shape_type,
                        left=left,
                        top=top,
                        width=width,
                        height=height,
                        text=shape_data.get("text"),
                        fill_color=shape_data.get("fill_color"),
                        font_size=shape_data.get("font_size"),
                        font_color=shape_data.get("font_color"),
                        bold=shape_data.get("bold"),
                        alignment=shape_data.get("alignment"),
                        line_color=shape_data.get("line_color"),
                        line_width=shape_data.get("line_width"),
                        rich_text=shape_data.get("rich_text"),
                        italic=shape_data.get("italic"),
                        underline=shape_data.get("underline"),
                        font_name=shape_data.get("font_name"),
                    )
                    added_count += 1

                if added_count > 0:
                    modifications.append(f"{added_count} shape(s) added")

            # Update notes
            if notes is not None:
                notes_slide = slide.notes_slide
                notes_tf = notes_slide.notes_text_frame
                notes_tf.text = notes
                modifications.append("notes updated")

            prs.save(path)

            if modifications:
                return (
                    f"Successfully modified slide {slide_number}: {', '.join(modifications)}. "
                    f"Use pptx_export_image + read_image to verify the visual result."
                )
            else:
                return f"No changes made to slide {slide_number}"

        except Exception as e:
            return f"Error modifying slide: {e}"
