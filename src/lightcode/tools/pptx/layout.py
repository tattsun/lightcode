"""PowerPoint layout helper tool."""

import os

from pptx import Presentation

from lightcode.tools.base import Tool

EMU_PER_INCH = 914400


def _iter_shapes(shapes):
    for shape in shapes:
        yield shape
        if hasattr(shape, "shapes"):
            try:
                yield from _iter_shapes(shape.shapes)
            except Exception:
                pass


def _shape_map(slide):
    result = {}
    for shape in _iter_shapes(slide.shapes):
        result[shape.shape_id] = shape
    return result


def _edge_x(shape, edge: str) -> int:
    if edge == "left":
        return shape.left
    if edge == "right":
        return shape.left + shape.width
    if edge == "center_x":
        return shape.left + shape.width // 2
    raise ValueError(f"Unsupported edge: {edge}")


def _edge_y(shape, edge: str) -> int:
    if edge == "top":
        return shape.top
    if edge == "bottom":
        return shape.top + shape.height
    if edge == "center_y":
        return shape.top + shape.height // 2
    raise ValueError(f"Unsupported edge: {edge}")


class PptxLayoutTool(Tool):
    """Tool for aligning and distributing shapes on a slide."""

    @property
    def name(self) -> str:
        return "pptx_layout"

    @property
    def description(self) -> str:
        return """Align, distribute, or snap shapes on a slide.

All distances are in inches. Use pptx_read to get shape_id values.

actions formats:
1) align
{"type":"align","alignment":"left|center|right|top|middle|bottom",
 "shape_ids":[1,2,3],"reference":"slide|first|last|shape","ref_shape_id":10}

2) distribute
{"type":"distribute","direction":"horizontal|vertical","shape_ids":[1,2,3],
 "spacing":0.25}
If spacing is omitted, it distributes using current min/max bounds.

3) snap
{"type":"snap","shape_id":1,"target_shape_id":2,
 "edge":"left|right|center_x|top|bottom|center_y",
 "target_edge":"left|right|center_x|top|bottom|center_y",
 "offset":0.1}
edge and target_edge must be both horizontal or both vertical.
"""

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
                "description": "Slide number to modify (1-based)",
                "required": True,
            },
            "actions": {
                "type": "array",
                "items": {"type": "object"},
                "description": (
                    "Layout actions. Supported types: align/distribute/snap. "
                    "See tool description for the exact fields and examples."
                ),
                "required": True,
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        slide_number = kwargs.get("slide_number")
        actions = kwargs.get("actions", [])

        if not path:
            return "Error: path is required"
        if slide_number is None:
            return "Error: slide_number is required"
        if not actions:
            return "Error: actions is required"
        if not os.path.exists(path):
            return f"Error: File not found: {path}"

        try:
            prs = Presentation(path)
            total_slides = len(prs.slides)
            if slide_number < 1 or slide_number > total_slides:
                return f"Error: Invalid slide number {slide_number}. File has {total_slides} slide(s)."

            slide = prs.slides[slide_number - 1]
            shape_map = _shape_map(slide)

            slide_w = prs.slide_width
            slide_h = prs.slide_height

            mods = []

            for action in actions:
                if isinstance(action, str):
                    return "Error: actions must be objects, not strings"

                action_type = action.get("type")
                if action_type == "align":
                    alignment = action.get("alignment")
                    shape_ids = action.get("shape_ids", [])
                    reference = action.get("reference", "slide")
                    ref_shape_id = action.get("ref_shape_id")

                    if not shape_ids or not alignment:
                        return "Error: align requires alignment and shape_ids"

                    shapes = [shape_map.get(sid) for sid in shape_ids if shape_map.get(sid)]
                    if not shapes:
                        continue

                    # Determine reference position
                    if reference == "shape":
                        if ref_shape_id is None or ref_shape_id not in shape_map:
                            return "Error: align reference=shape requires valid ref_shape_id"
                        ref = shape_map[ref_shape_id]
                        ref_left = ref.left
                        ref_right = ref.left + ref.width
                        ref_top = ref.top
                        ref_bottom = ref.top + ref.height
                        ref_cx = ref.left + ref.width // 2
                        ref_cy = ref.top + ref.height // 2
                    elif reference == "first":
                        ref = shapes[0]
                        ref_left = ref.left
                        ref_right = ref.left + ref.width
                        ref_top = ref.top
                        ref_bottom = ref.top + ref.height
                        ref_cx = ref.left + ref.width // 2
                        ref_cy = ref.top + ref.height // 2
                    elif reference == "last":
                        ref = shapes[-1]
                        ref_left = ref.left
                        ref_right = ref.left + ref.width
                        ref_top = ref.top
                        ref_bottom = ref.top + ref.height
                        ref_cx = ref.left + ref.width // 2
                        ref_cy = ref.top + ref.height // 2
                    else:
                        # slide reference
                        ref_left = 0
                        ref_right = slide_w
                        ref_top = 0
                        ref_bottom = slide_h
                        ref_cx = slide_w // 2
                        ref_cy = slide_h // 2

                    for shape in shapes:
                        if alignment == "left":
                            shape.left = ref_left
                        elif alignment == "center":
                            shape.left = ref_cx - shape.width // 2
                        elif alignment == "right":
                            shape.left = ref_right - shape.width
                        elif alignment == "top":
                            shape.top = ref_top
                        elif alignment == "middle":
                            shape.top = ref_cy - shape.height // 2
                        elif alignment == "bottom":
                            shape.top = ref_bottom - shape.height
                        else:
                            return f"Error: Unsupported alignment '{alignment}'"

                    mods.append(f"aligned {len(shapes)} shape(s) {alignment}")

                elif action_type == "distribute":
                    direction = action.get("direction")
                    shape_ids = action.get("shape_ids", [])
                    spacing_in = action.get("spacing")

                    if not shape_ids or direction not in ("horizontal", "vertical"):
                        return "Error: distribute requires direction and shape_ids"

                    shapes = [shape_map.get(sid) for sid in shape_ids if shape_map.get(sid)]
                    if len(shapes) < 3:
                        return "Error: distribute requires at least 3 shapes"

                    if direction == "horizontal":
                        shapes = sorted(shapes, key=lambda s: s.left)
                        total = sum(s.width for s in shapes)
                        min_pos = shapes[0].left
                        max_pos = shapes[-1].left + shapes[-1].width
                        if spacing_in is None:
                            available = max_pos - min_pos - total
                            if available < 0:
                                return "Error: distribute horizontal has negative spacing"
                            gap = available // (len(shapes) - 1)
                        else:
                            gap = int(float(spacing_in) * EMU_PER_INCH)
                        prev = shapes[0]
                        pos = prev.left
                        for s in shapes[1:]:
                            pos = prev.left + prev.width + gap
                            s.left = pos
                            prev = s
                    else:
                        shapes = sorted(shapes, key=lambda s: s.top)
                        total = sum(s.height for s in shapes)
                        min_pos = shapes[0].top
                        max_pos = shapes[-1].top + shapes[-1].height
                        if spacing_in is None:
                            available = max_pos - min_pos - total
                            if available < 0:
                                return "Error: distribute vertical has negative spacing"
                            gap = available // (len(shapes) - 1)
                        else:
                            gap = int(float(spacing_in) * EMU_PER_INCH)
                        prev = shapes[0]
                        pos = prev.top
                        for s in shapes[1:]:
                            pos = prev.top + prev.height + gap
                            s.top = pos
                            prev = s

                    mods.append(f"distributed {len(shapes)} shape(s) {direction}")

                elif action_type == "snap":
                    shape_id = action.get("shape_id")
                    target_shape_id = action.get("target_shape_id")
                    edge = action.get("edge")
                    target_edge = action.get("target_edge", edge)
                    offset_in = action.get("offset", 0)

                    if shape_id is None or target_shape_id is None or not edge:
                        return "Error: snap requires shape_id, target_shape_id, and edge"
                    if shape_id not in shape_map or target_shape_id not in shape_map:
                        return "Error: snap shape_id or target_shape_id not found"

                    shape = shape_map[shape_id]
                    target = shape_map[target_shape_id]
                    offset = int(float(offset_in) * EMU_PER_INCH)

                    if edge in ("left", "right", "center_x"):
                        if target_edge not in ("left", "right", "center_x"):
                            return "Error: target_edge must be left/right/center_x for horizontal snap"
                        target_pos = _edge_x(target, target_edge)
                        if edge == "left":
                            shape.left = target_pos + offset
                        elif edge == "right":
                            shape.left = target_pos - shape.width + offset
                        elif edge == "center_x":
                            shape.left = target_pos - shape.width // 2 + offset
                    elif edge in ("top", "bottom", "center_y"):
                        if target_edge not in ("top", "bottom", "center_y"):
                            return "Error: target_edge must be top/bottom/center_y for vertical snap"
                        target_pos = _edge_y(target, target_edge)
                        if edge == "top":
                            shape.top = target_pos + offset
                        elif edge == "bottom":
                            shape.top = target_pos - shape.height + offset
                        elif edge == "center_y":
                            shape.top = target_pos - shape.height // 2 + offset
                    else:
                        return f"Error: Unsupported edge '{edge}'"

                    mods.append(f"snapped shape {shape_id} to {target_shape_id} {edge}")
                else:
                    return f"Error: Unsupported action type '{action_type}'"

            prs.save(path)

            if mods:
                return f"Successfully updated layout on slide {slide_number}: " + "; ".join(mods)
            return f"No layout changes applied to slide {slide_number}"

        except Exception as e:
            return f"Error applying layout: {e}"
