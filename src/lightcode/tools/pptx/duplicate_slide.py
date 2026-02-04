"""PowerPoint slide duplication tool."""

import os
import re
import uuid
from copy import deepcopy

from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.oxml.ns import qn

from lightcode.tools.base import Tool

# Pattern to match GUID format: {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
GUID_PATTERN = re.compile(
    r"^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$"
)

# Pattern to extract number from partname (e.g., data5.xml -> 5)
PARTNAME_NUM_PATTERN = re.compile(r"(\d+)\.[a-z]+$")

REL_ATTRS = (
    qn("r:id"),
    qn("r:embed"),
    qn("r:link"),
    # SmartArt (diagram) relationship attributes
    qn("r:dm"),  # diagram data
    qn("r:lo"),  # diagram layout
    qn("r:qs"),  # diagram quick style
    qn("r:cs"),  # diagram colors
)

# Relationship types that require part duplication (not sharing)
DIAGRAM_RELTYPES = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramData",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramLayout",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramColors",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramQuickStyle",
    "http://schemas.microsoft.com/office/2007/relationships/diagramDrawing",
)


def _find_next_partname(package, base_path, prefix, extension):
    """Find next available partname number for a given path pattern.

    Args:
        package: The OPC package
        base_path: Base directory path (e.g., '/ppt/diagrams')
        prefix: Filename prefix (e.g., 'data')
        extension: File extension (e.g., '.xml')

    Returns:
        PackURI for the next available partname
    """
    existing_nums = []
    pattern = re.compile(rf"{re.escape(prefix)}(\d+){re.escape(extension)}$")

    for part in package.iter_parts():
        pn = str(part.partname)
        if pn.startswith(base_path):
            m = pattern.search(pn)
            if m:
                existing_nums.append(int(m.group(1)))

    next_num = max(existing_nums, default=0) + 1
    return PackURI(f"{base_path}/{prefix}{next_num}{extension}")


def _clone_part(package, original_part):
    """Create a clone of a part with a new unique partname.

    Args:
        package: The OPC package
        original_part: The part to clone

    Returns:
        New Part instance with copied content
    """
    partname = str(original_part.partname)

    # Extract base path, prefix, and extension
    # e.g., /ppt/diagrams/data5.xml -> /ppt/diagrams, data, .xml
    base_path = partname.rsplit("/", 1)[0]
    filename = partname.rsplit("/", 1)[1]

    m = PARTNAME_NUM_PATTERN.search(filename)
    if m:
        prefix = filename[: m.start(1)]
        extension = filename[m.end(1) :]
    else:
        # Fallback: use entire filename as prefix
        prefix = filename.rsplit(".", 1)[0]
        extension = "." + filename.rsplit(".", 1)[1] if "." in filename else ""

    new_partname = _find_next_partname(package, base_path, prefix, extension)

    return Part.load(
        new_partname, original_part.content_type, package, original_part.blob
    )


def _copy_relationships(source_slide, target_slide, package):
    """Copy relationships and return rId mapping.

    Diagram parts are cloned (new copies created), while other parts
    like images are shared (referenced).

    Args:
        source_slide: Source slide to copy from
        target_slide: Target slide to copy to
        package: The OPC package (for creating new parts)

    Returns:
        dict: Mapping of old rId -> new rId
    """
    rel_id_map = {}
    target_rels = target_slide.part.rels

    for rel in source_slide.part.rels.values():
        # Skip layout (already set via add_slide) and notes (handled separately)
        if rel.reltype in (RT.SLIDE_LAYOUT, RT.NOTES_SLIDE):
            continue

        if rel.is_external:
            new_rid = target_rels.get_or_add_ext_rel(rel.reltype, rel.target_ref)
        elif rel.reltype in DIAGRAM_RELTYPES:
            # Diagram parts must be cloned (not shared)
            new_part = _clone_part(package, rel._target)
            new_rid = target_slide.part.relate_to(new_part, rel.reltype)
        else:
            # Other internal parts (images, etc.) can be shared
            new_rid = target_rels.get_or_add(rel.reltype, rel._target)

        rel_id_map[rel.rId] = new_rid

    return rel_id_map


def _update_rids_in_element(element, rel_id_map):
    """Update all rId references in an XML element tree."""
    for el in element.iter():
        for attr in REL_ATTRS:
            if attr in el.attrib:
                old_rid = el.attrib[attr]
                if old_rid in rel_id_map:
                    el.attrib[attr] = rel_id_map[old_rid]


def _regenerate_guids(element):
    """Regenerate GUIDs in creationId and fld elements to ensure uniqueness."""
    for el in element.iter():
        tag_name = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        # creationId elements have id attribute with GUID
        if tag_name == "creationId":
            if "id" in el.attrib and GUID_PATTERN.match(el.attrib["id"]):
                el.attrib["id"] = "{" + str(uuid.uuid4()).upper() + "}"
        # fld (field) elements also have id attribute with GUID
        elif tag_name == "fld":
            if "id" in el.attrib and GUID_PATTERN.match(el.attrib["id"]):
                el.attrib["id"] = "{" + str(uuid.uuid4()).upper() + "}"


def _copy_slide_shapes(source_slide, target_slide, rel_id_map):
    """Copy all shapes from source to target slide with rId remapping."""
    # Remove existing shapes from target (leave required group properties)
    for shape in list(target_slide.shapes):
        sp = shape._element
        target_slide.shapes._spTree.remove(sp)

    # Insert shapes in original order to preserve z-order
    for shape in source_slide.shapes:
        new_el = deepcopy(shape._element)
        _update_rids_in_element(new_el, rel_id_map)
        _regenerate_guids(new_el)
        target_slide.shapes._spTree.insert_element_before(new_el, "p:extLst")


def _copy_slide_background(source_slide, target_slide, rel_id_map):
    """Copy background settings with rId remapping."""
    try:
        src_bg = source_slide._element.cSld.bg
        if src_bg is not None:
            new_bg = deepcopy(src_bg)
            _update_rids_in_element(new_bg, rel_id_map)
            target_slide._element.cSld.bg = new_bg
    except Exception:
        # Background copying is best-effort
        pass


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

            # 1. First: copy relationships and get rId mapping
            rel_id_map = _copy_relationships(source_slide, new_slide, prs.part.package)

            # 2. Then: copy shapes with rId remapping
            _copy_slide_shapes(source_slide, new_slide, rel_id_map)

            # 3. Copy background with rId remapping
            _copy_slide_background(source_slide, new_slide, rel_id_map)

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
