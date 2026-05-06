# Copyright (c) 2019-2024 Manfred Moitzi
# License: MIT License
from __future__ import annotations
from typing import TYPE_CHECKING, Iterable, Optional, Iterator
from typing_extensions import Self
import copy
from dataclasses import dataclass, field
from ezdxf.math import Vec3, Matrix44
from ezdxf.lldxf.tags import Tags, group_tags
from ezdxf.lldxf.attributes import (
    DXFAttr,
    DXFAttributes,
    DefSubclass,
    XType,
    group_code_mapping,
)
from ezdxf.lldxf import const
from ezdxf.entities import factory
from .dxfentity import base_class, SubclassProcessor, DXFEntity, DXFTagStorage
from .dxfgfx import DXFGraphic, acdb_entity
from .dxfobj import DXFObject
from .objectcollection import ObjectCollection
from .copy import default_copy

if TYPE_CHECKING:
    from ezdxf.entities import DXFNamespace
    from ezdxf.lldxf.tagwriter import AbstractTagWriter
    from ezdxf.document import Drawing

__all__ = [
    "AcadTable",
    "AcadTableBlockAttributeValue",
    "AcadTableCell",
    "AcadTableData",
    "TableStyleCellStyle",
    "TableStyleData",
    "AcadTableLinkedCell",
    "AcadTableLinkedCellContent",
    "AcadTableLinkedData",
    "AcadTableBlockContent",
    "TableContent",
    "TableStyle",
    "TableStyleManager",
    "acad_table_to_block",
    "read_acad_table_content",
]


@dataclass
class AcadTableBlockAttributeValue:
    handle: str
    text: str = ""
    index: int = 0


@dataclass
class AcadTableLinkedCellContent:
    content_type: int = 0
    text: str = ""
    block_record_handle: Optional[str] = None
    block_scale: Optional[float] = None
    alignment: Optional[int] = None
    block_attributes: list[AcadTableBlockAttributeValue] = field(default_factory=list)

    @property
    def is_block_content(self) -> bool:
        return self.content_type == 4


@dataclass
class AcadTableLinkedCell:
    row: int
    col: int
    contents: list[AcadTableLinkedCellContent] = field(default_factory=list)


@dataclass
class AcadTableLinkedData:
    n_rows: int = 0
    n_cols: int = 0
    cells: list[AcadTableLinkedCell] = field(default_factory=list)

    @classmethod
    def from_tags(cls, tags: Tags, *, n_rows: int = 0, n_cols: int = 0) -> "AcadTableLinkedData":
        data = cls(n_rows=n_rows, n_cols=n_cols)
        cell_index = 0
        index = 0
        while index < len(tags):
            tag = tags[index]
            if tag.code == 1 and tag.value == "LINKEDTABLEDATACELL_BEGIN":
                end = _find_marker_end(tags, index + 1, 309, "LINKEDTABLEDATACELL_END")
                cell_tags = Tags(tags[index : end + 1])
                data.cells.append(_parse_linked_table_cell(cell_tags, cell_index, n_cols))
                cell_index += 1
                index = end + 1
                continue
            index += 1
        return data

    def rows(self) -> list[list[AcadTableLinkedCell]]:
        if self.n_rows <= 0 or self.n_cols <= 0:
            return [list(self.cells)] if len(self.cells) else []
        rows: list[list[AcadTableLinkedCell]] = []
        for index in range(self.n_rows):
            start = index * self.n_cols
            rows.append(self.cells[start : start + self.n_cols])
        return rows


@dataclass
class AcadTableCell:
    row: int
    col: int
    cell_type: int = 1
    flags: int = 0
    merged_value: int = 0
    autofit_flag: int = 0
    border_width: int = 0
    border_height: int = 0
    override_flags: int = 0
    virtual_edge_flag: int = 0
    rotation: float = 0.0
    text: str = ""
    block_record_handle: Optional[str] = None
    block_scale: float = 1.0
    block_attribute_count: int = 0
    text_height: Optional[float] = None
    alignment: Optional[int] = None
    text_style: Optional[str] = None
    content_color: Optional[int] = None
    fill_color: Optional[int] = None
    fill_true_color: Optional[int] = None
    fill_enabled: Optional[int] = None
    field_handle: Optional[str] = None
    block_attributes: list[AcadTableBlockAttributeValue] = field(default_factory=list)
    linked_cell_contents: list[AcadTableLinkedCellContent] = field(default_factory=list)

    @property
    def is_text_cell(self) -> bool:
        return self.cell_type == 1

    @property
    def is_block_cell(self) -> bool:
        return self.cell_type == 2

    @property
    def has_block_attributes(self) -> bool:
        return len(self.block_attributes) > 0

    @property
    def has_field(self) -> bool:
        return self.field_handle is not None


@dataclass
class AcadTableData:
    n_rows: int = 0
    n_cols: int = 0
    row_heights: list[float] = field(default_factory=list)
    col_widths: list[float] = field(default_factory=list)
    cells: list[AcadTableCell] = field(default_factory=list)
    suppress_title: Optional[int] = None
    suppress_column_header: Optional[int] = None
    trailing_tags: Tags = field(default_factory=Tags)

    def rows(self) -> list[list[AcadTableCell]]:
        if self.n_rows <= 0 or self.n_cols <= 0:
            return [list(self.cells)] if len(self.cells) else []
        rows: list[list[AcadTableCell]] = []
        for index in range(self.n_rows):
            start = index * self.n_cols
            rows.append(self.cells[start : start + self.n_cols])
        return rows

    def text_content(self) -> list[list[str]]:
        return [[cell.text for cell in row] for row in self.rows()]


@dataclass
class TableStyleCellStyle:
    text_style: str = ""
    text_height: float = 0.0
    alignment: int = 0
    text_color: int = 0
    fill_color: int = 0
    fill_enabled: int = 0
    data_type: int = 0
    unit_type: int = 0
    format_string: str = ""
    border_lineweights: dict[str, int] = field(default_factory=dict)
    border_visibility: dict[str, int] = field(default_factory=dict)
    border_colors: dict[str, int] = field(default_factory=dict)


@dataclass
class TableStyleData:
    flow_direction: int = 0
    flags: int = 0
    horizontal_cell_margin: float = 0.0
    vertical_cell_margin: float = 0.0
    suppress_title: int = 0
    suppress_column_header: int = 0
    cell_styles: list[TableStyleCellStyle] = field(default_factory=list)
    trailing_tags: Tags = field(default_factory=Tags)

    @property
    def title_style(self) -> Optional[TableStyleCellStyle]:
        return self.cell_styles[0] if len(self.cell_styles) > 0 else None

    @property
    def header_style(self) -> Optional[TableStyleCellStyle]:
        return self.cell_styles[1] if len(self.cell_styles) > 1 else None

    @property
    def data_style(self) -> Optional[TableStyleCellStyle]:
        return self.cell_styles[2] if len(self.cell_styles) > 2 else None


def _parse_acad_table_content(dxf, tags: Tags) -> AcadTableData:
    start = 1 if len(tags) and tags[0].code == 100 else 0
    data = AcadTableData()
    set_attrib = dxf.unprotected_set

    index = start
    version_loaded = False
    while index < len(tags):
        tag = tags[index]
        code = tag.code
        if code in (141, 142, 171):
            break
        if code == 280:
            if not version_loaded:
                set_attrib("version", int(tag.value))
                version_loaded = True
            elif data.suppress_title is None:
                data.suppress_title = int(tag.value)
        elif code == 281:
            if data.suppress_column_header is None:
                data.suppress_column_header = int(tag.value)
        elif code == 342:
            set_attrib("table_style_id", str(tag.value))
        elif code == 343:
            set_attrib("block_record_handle", str(tag.value))
        elif code == 11:
            set_attrib("horizontal_direction", tag.value)
        elif code == 90 and not dxf.hasattr("table_value"):
            set_attrib("table_value", int(tag.value))
        elif code == 91 and not dxf.hasattr("n_rows"):
            set_attrib("n_rows", int(tag.value))
        elif code == 92 and not dxf.hasattr("n_cols"):
            set_attrib("n_cols", int(tag.value))
        elif code == 93 and not dxf.hasattr("override_flag"):
            set_attrib("override_flag", int(tag.value))
        elif code == 94 and not dxf.hasattr("border_color_override_flag"):
            set_attrib("border_color_override_flag", int(tag.value))
        elif code == 95 and not dxf.hasattr("border_lineweight_override_flag"):
            set_attrib("border_lineweight_override_flag", int(tag.value))
        elif code == 96 and not dxf.hasattr("border_visibility_override_flag"):
            set_attrib("border_visibility_override_flag", int(tag.value))
        index += 1

    data.n_rows = int(dxf.get("n_rows", 0))
    data.n_cols = int(dxf.get("n_cols", 0))

    while index < len(tags) and tags[index].code == 141:
        data.row_heights.append(float(tags[index].value))
        index += 1
    while index < len(tags) and tags[index].code == 142:
        data.col_widths.append(float(tags[index].value))
        index += 1

    expected_cells = data.n_rows * data.n_cols
    cells: list[AcadTableCell] = []
    while index < len(tags) and (expected_cells == 0 or len(cells) < expected_cells):
        if tags[index].code != 171:
            break
        start_index = index
        index += 1
        while index < len(tags) and tags[index].code != 171:
            index += 1
        cells.append(_parse_acad_table_cell(tags[start_index:index], len(cells), data.n_cols))

    data.cells = cells
    data.trailing_tags = Tags(tags[index:])
    return data


def _parse_acad_table_cell(tags: Tags, cell_index: int, n_cols: int) -> AcadTableCell:
    row = cell_index // n_cols if n_cols else 0
    col = cell_index % n_cols if n_cols else cell_index
    cell = AcadTableCell(row=row, col=col)

    in_value = False
    plain_value_tags: list[str] = []
    chunked_value_tags: list[str] = []
    for code, value in tags:
        if in_value:
            if code == 304 and value == "ACVALUE_END":
                in_value = False
                continue
            if code == 302:
                chunked_value_tags.append(str(value))
            elif code in (1, 2, 3):
                plain_value_tags.append(str(value))
            continue

        if code == 171 and cell.cell_type == 1:
            cell.cell_type = int(value)
        elif code == 172:
            cell.flags = int(value)
        elif code == 173:
            cell.merged_value = int(value)
        elif code == 174:
            cell.autofit_flag = int(value)
        elif code == 175:
            cell.border_width = int(value)
        elif code == 176:
            cell.border_height = int(value)
        elif code == 91:
            cell.override_flags = int(value)
        elif code == 178:
            cell.virtual_edge_flag = int(value)
        elif code == 145:
            cell.rotation = float(value)
        elif code == 340:
            cell.block_record_handle = str(value)
        elif code == 144:
            cell.block_scale = float(value)
        elif code == 179:
            cell.block_attribute_count = int(value)
        elif code == 140:
            cell.text_height = float(value)
        elif code == 170:
            cell.alignment = int(value)
        elif code == 7:
            cell.text_style = str(value)
        elif code == 64:
            cell.content_color = int(value)
        elif code == 63:
            cell.fill_color = int(value)
        elif code in (420, 421):
            cell.fill_true_color = int(value)
        elif code == 283:
            cell.fill_enabled = int(value)
        elif code == 344:
            cell.field_handle = str(value)
        elif code == 301 and value == "CELL_VALUE":
            in_value = True

    cell.text = "".join(chunked_value_tags or plain_value_tags)
    return cell


def _find_marker_end(tags: Tags, start: int, end_code: int, end_value: str) -> int:
    index = start
    while index < len(tags):
        tag = tags[index]
        if tag.code == end_code and tag.value == end_value:
            return index
        index += 1
    raise const.DXFStructureError(f"missing marker end tag: {end_value}")


def _parse_linked_table_cell(tags: Tags, cell_index: int, n_cols: int) -> AcadTableLinkedCell:
    row = cell_index // n_cols if n_cols else 0
    col = cell_index % n_cols if n_cols else cell_index
    cell = AcadTableLinkedCell(row=row, col=col)

    index = 0
    while index < len(tags):
        tag = tags[index]
        if tag.code == 1 and tag.value == "CELLCONTENT_BEGIN":
            end = _find_marker_end(tags, index + 1, 309, "CELLCONTENT_END")
            cell.contents.append(_parse_linked_cell_content(Tags(tags[index : end + 1])))
            index = end + 1
            continue
        index += 1
    return cell


def _parse_linked_cell_content(tags: Tags) -> AcadTableLinkedCellContent:
    content = AcadTableLinkedCellContent()
    pending_attr: Optional[AcadTableBlockAttributeValue] = None
    pending_handle: Optional[str] = None
    in_value = False
    plain_value_tags: list[str] = []
    chunked_value_tags: list[str] = []

    for code, value in tags:
        if in_value:
            if code == 304 and value == "ACVALUE_END":
                in_value = False
                continue
            if code == 302:
                chunked_value_tags.append(str(value))
            elif code in (1, 2, 3):
                plain_value_tags.append(str(value))
            continue

        if code == 90 and content.content_type == 0:
            content.content_type = int(value)
        elif code == 340:
            content.block_record_handle = str(value)
        elif code == 144:
            content.block_scale = float(value)
        elif code == 170:
            content.alignment = int(value)
        elif code == 330:
            pending_handle = str(value)
        elif code == 301 and value == "VALUE":
            in_value = True
        elif code == 301 and pending_handle is not None:
            pending_attr = AcadTableBlockAttributeValue(handle=pending_handle, text=str(value))
            content.block_attributes.append(pending_attr)
            pending_handle = None
        elif code == 92 and pending_attr is not None:
            pending_attr.index = int(value)
            pending_attr = None

    content.text = "".join(chunked_value_tags or plain_value_tags)
    return content


def _parse_table_style(tags: Tags) -> TableStyleData:
    start = 1 if len(tags) and tags[0].code == 100 else 0
    data = TableStyleData()
    index = start

    if index < len(tags) and tags[index].code == 280:
        index += 1  # version tag handled by dxfattribs loader
    if index < len(tags) and tags[index].code == 3:
        index += 1  # name tag handled by dxfattribs loader
    if index < len(tags) and tags[index].code == 70:
        data.flow_direction = int(tags[index].value)
        index += 1
    if index < len(tags) and tags[index].code == 71:
        data.flags = int(tags[index].value)
        index += 1
    if index < len(tags) and tags[index].code == 40:
        data.horizontal_cell_margin = float(tags[index].value)
        index += 1
    if index < len(tags) and tags[index].code == 41:
        data.vertical_cell_margin = float(tags[index].value)
        index += 1
    if index < len(tags) and tags[index].code == 280:
        data.suppress_title = int(tags[index].value)
        index += 1
    if index < len(tags) and tags[index].code == 281:
        data.suppress_column_header = int(tags[index].value)
        index += 1

    while index < len(tags):
        if tags[index].code != 7:
            break
        cell_style = TableStyleCellStyle(text_style=str(tags[index].value))
        index += 1
        if index < len(tags) and tags[index].code == 140:
            cell_style.text_height = float(tags[index].value)
            index += 1
        if index < len(tags) and tags[index].code == 170:
            cell_style.alignment = int(tags[index].value)
            index += 1
        if index < len(tags) and tags[index].code == 62:
            cell_style.text_color = int(tags[index].value)
            index += 1
        if index < len(tags) and tags[index].code == 63:
            cell_style.fill_color = int(tags[index].value)
            index += 1
        if index < len(tags) and tags[index].code == 283:
            cell_style.fill_enabled = int(tags[index].value)
            index += 1
        if index < len(tags) and tags[index].code == 90:
            cell_style.data_type = int(tags[index].value)
            index += 1
        if index < len(tags) and tags[index].code == 91:
            cell_style.unit_type = int(tags[index].value)
            index += 1
        if index < len(tags) and tags[index].code == 1:
            cell_style.format_string = str(tags[index].value)
            index += 1
        for code, name in ((274, "top"), (275, "right"), (276, "bottom"), (277, "left"), (278, "vertical"), (279, "horizontal")):
            if index < len(tags) and tags[index].code == code:
                cell_style.border_lineweights[name] = int(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == code + 10:
                cell_style.border_visibility[name] = int(tags[index].value)
                index += 1
            color_code = 64 if code == 274 else 65 if code == 275 else 66 if code == 276 else 67 if code == 277 else 68 if code == 278 else 69
            if index < len(tags) and tags[index].code == color_code:
                cell_style.border_colors[name] = int(tags[index].value)
                index += 1
        data.cell_styles.append(cell_style)

    data.trailing_tags = Tags(tags[index:])
    return data


acdb_block_reference = DefSubclass(
    "AcDbBlockReference",
    {
        # Block name: an anonymous block begins with a *T value
        "geometry": DXFAttr(2),
        # Insertion point:
        "insert": DXFAttr(10, xtype=XType.point3d, default=Vec3(0, 0, 0)),
    },
)
acdb_block_reference_group_codes = group_code_mapping(acdb_block_reference)

acdb_table = DefSubclass(
    "AcDbTable",
    {
        # Table data version number: 0 = 2010
        "version": DXFAttr(280),
        # Hard of the TABLESTYLE object:
        "table_style_id": DXFAttr(342),
        # Handle of the associated anonymous BLOCK containing the graphical
        # representation:
        "block_record_handle": DXFAttr(343),
        # Horizontal direction vector:
        "horizontal_direction": DXFAttr(11),
        # Flag for table value (unsigned integer):
        "table_value": DXFAttr(90),
        # Number of rows:
        "n_rows": DXFAttr(91),
        # Number of columns:
        "n_cols": DXFAttr(92),
        # Flag for an override:
        "override_flag": DXFAttr(93),
        # Flag for an override of border color:
        "border_color_override_flag": DXFAttr(94),
        # Flag for an override of border lineweight:
        "border_lineweight_override_flag": DXFAttr(95),
        # Flag for an override of border visibility:
        "border_visibility_override_flag": DXFAttr(96),
        # 141: Row height; this value is repeated, 1 value per row
        # 142: Column height; this value is repeated, 1 value per column
        # for every cell:
        #      171: Cell type; this value is repeated, 1 value per cell:
        #           1 = text type
        #           2 = block type
        #      172: Cell flag value; this value is repeated, 1 value per cell
        #      173: Cell merged value; this value is repeated, 1 value per cell
        #      174: Boolean flag indicating if the autofit option is set for the
        #           cell; this value is repeated, 1 value per cell
        #      175: Cell border width (applicable only for merged cells); this
        #           value is repeated, 1 value per cell
        #      176: Cell border height (applicable for merged cells); this value
        #           is repeated, 1 value per cell
        #       91: Cell override flag; this value is repeated, 1 value per cell
        #           (from AutoCAD 2007)
        #      178: Flag value for a virtual edge
        #      145: Rotation value (real; applicable for a block-type cell and
        #           a text-type cell)
        #      344: Hard pointer ID of the FIELD object. This applies only to a
        #           text-type cell. If the text in the cell contains one or more
        #           fields, only the ID of the FIELD object is saved.
        #           The text string (group codes 1 and 3) is ignored
        #        1: Text string in a cell. If the string is shorter than 250
        #           characters, all characters appear in code 1.
        #           If the string is longer than 250 characters, it is divided
        #           into chunks of 250 characters.
        #           The chunks are contained in one or more code 2 codes.
        #           If code 2 codes are used, the last group is a code 1 and is
        #           shorter than 250 characters.
        #           This value applies only to text-type cells and is repeated,
        #           1 value per cell
        #        2: Text string in a cell, in 250-character chunks; optional.
        #           This value applies only to text-type cells and is repeated,
        #           1 value per cell
        #      340: Hard-pointer ID of the block table record.
        #           This value applies only to block-type cells and is repeated,
        #           1 value per cell
        #      144: Block scale (real). This value applies only to block-type
        #           cells and is repeated, 1 value per cell
        #      176: Number of attribute definitions in the block table record
        #           (applicable only to a block-type cell)
        #      for every ATTDEF:
        #           331: Soft pointer ID of the attribute definition in the
        #                block table record, referenced by group code 179
        #                (applicable only for a block-type cell). This value is
        #                repeated once per attribute definition
        #           300: Text string value for an attribute definition, repeated
        #                once per attribute definition and applicable only for
        #                a block-type cell
        #        7: Text style name (string); override applied at the cell level
        #      140: Text height value; override applied at the cell level
        #      170: Cell alignment value; override applied at the cell level
        #       64: Value for the color of cell content; override applied at the
        #           cell level
        #       63: Value for the background (fill) color of cell content;
        #           override applied at the cell level
        #       69: True color value for the top border of the cell;
        #           override applied at the cell level
        #       65: True color value for the right border of the cell;
        #           override applied at the cell level
        #       66: True color value for the bottom border of the cell;
        #           override applied at the cell level
        #       68: True color value for the left border of the cell;
        #           override applied at the cell level
        #      279: Lineweight for the top border of the cell;
        #           override applied at the cell level
        #      275: Lineweight for the right border of the cell;
        #           override applied at the cell level
        #      276: Lineweight for the bottom border of the cell;
        #           override applied at the cell level
        #      278: Lineweight for the left border of the cell;
        #           override applied at the cell level
        #      283: Boolean flag for whether the fill color is on;
        #           override applied at the cell level
        #      289: Boolean flag for the visibility of the top border of the cell;
        #           override applied at the cell level
        #      285: Boolean flag for the visibility of the right border of the cell;
        #           override applied at the cell level
        #      286: Boolean flag for the visibility of the bottom border of the cell;
        #           override applied at the cell level
        #      288: Boolean flag for the visibility of the left border of the cell;
        #           override applied at the cell level
        #       70: Flow direction;
        #           override applied at the table entity level
        #       40: Horizontal cell margin;
        #           override applied at the table entity level
        #       41: Vertical cell margin;
        #           override applied at the table entity level
        #      280: Flag for whether the title is suppressed;
        #           override applied at the table entity level
        #      281: Flag for whether the header row is suppressed;
        #           override applied at the table entity level
        #        7: Text style name (string);
        #           override applied at the table entity level.
        #           There may be one entry for each cell type
        #      140: Text height (real);
        #           override applied at the table entity level.
        #           There may be one entry for each cell type
        #      170: Cell alignment (integer);
        #           override applied at the table entity level.
        #           There may be one entry for each cell type
        #       63: Color value for cell background or for the vertical, left
        #           border of the table; override applied at the table entity
        #           level. There may be one entry for each cell type
        #       64: Color value for cell content or for the horizontal, top
        #           border of the table; override applied at the table entity
        #           level. There may be one entry for each cell type
        #       65: Color value for the horizontal, inside border lines;
        #           override applied at the table entity level
        #       66: Color value for the horizontal, bottom border lines;
        #           override applied at the table entity level
        #       68: Color value for the vertical, inside border lines;
        #           override applied at the table entity level
        #       69: Color value for the vertical, right border lines;
        #           override applied at the table entity level
        #      283: Flag for whether background color is enabled (default = 0);
        #           override applied at the table entity level.
        #           There may be one entry for each cell type: 0/1 = Disabled/Enabled
        #      274-279: Lineweight for each border type of the cell (default = kLnWtByBlock);
        #               override applied at the table entity level.
        #               There may be one group for each cell type
        #      284-289: Flag for visibility of each border type of the cell (default = 1);
        #               override applied at the table entity level.
        #               There may be one group for each cell type: 0/1 = Invisible/Visible
        #  97: Standard/title/header row data type
        #  98: Standard/title/header row unit type
        #   4: Standard/title/header row format string
        #
        # AutoCAD 2007 and before:
        # 177: Cell override flag value (before AutoCAD 2007)
        #  92: Extended cell flags (from AutoCAD 2007), COLLISION: group code
        #      also used by n_cols
        # 301: Text string in a cell. If the string is shorter than 250
        #      characters, all characters appear in code 302.
        #      If the string is longer than 250 characters, it is divided into
        #      chunks of 250 characters.
        #      The chunks are contained in one or more code 303 codes.
        #      If code 393 codes are used, the last group is a code 1 and is
        #      shorter than 250 characters.
        #      --- WRONG: The text is divided into chunks of group code 2 and the last
        #          chuck has group code 1.
        #      This value applies only to text-type cells and is repeated,
        #      1 value per cell (from AutoCAD 2007)
        # 302: Text string in a cell, in 250-character chunks; optional.
        #      This value applies only to text-type cells and is repeated,
        #      302 value per cell (from AutoCAD 2007)
        #      --- WRONG: 302 contains all the text as a long string, tested with more
        #          than 66000 characters
        # BricsCAD writes long text in cells with both methods: 302 & (2, 2, 2, ..., 1)
        #
        # REMARK from Autodesk:
        # Group code 178 is a flag value for a virtual edge. A virtual edge is
        # used when a grid line is shared by two cells.
        # For example, if a table contains one row and two columns and it
        # contains cell A and cell B, the central grid line
        # contains the right edge of cell A and the left edge of cell B.
        # One edge is real, and the other edge is virtual.
        # The virtual edge points to the real edge; both edges have the same
        # set of properties, including color, lineweight, and visibility.
    },
)
acdb_table_group_codes = group_code_mapping(acdb_table)


# todo: implement ACAD_TABLE
class AcadTable(DXFGraphic):
    """DXF ACAD_TABLE entity"""

    DXFTYPE = "ACAD_TABLE"
    DXFATTRIBS = DXFAttributes(
        base_class, acdb_entity, acdb_block_reference, acdb_table
    )
    MIN_DXF_VERSION_FOR_EXPORT = const.DXF2007

    def __init__(self):
        super().__init__()
        self.data: Optional[AcadTableData] = None

    def copy_data(self, entity: Self, copy_strategy=default_copy) -> None:
        """Copy data."""
        assert isinstance(entity, AcadTable)
        entity.data = copy.deepcopy(self.data)

    def load_dxf_attribs(
        self, processor: Optional[SubclassProcessor] = None
    ) -> DXFNamespace:
        dxf = super().load_dxf_attribs(processor)
        if processor:
            processor.fast_load_dxfattribs(
                dxf, acdb_block_reference_group_codes, subclass=2
            )
            tags = processor.subclass_by_index(3)
            if tags is not None:
                self.load_table(tags)
        return dxf

    def load_table(self, tags: Tags):
        self.data = _parse_acad_table_content(self.dxf, tags)

    def export_entity(self, tagwriter: AbstractTagWriter) -> None:
        """Export entity specific data as DXF tags."""
        super().export_entity(tagwriter)
        tagwriter.write_tag2(const.SUBCLASS_MARKER, acdb_block_reference.name)
        self.dxf.export_dxf_attribs(tagwriter, ["geometry", "insert"])
        tagwriter.write_tag2(const.SUBCLASS_MARKER, acdb_table.name)
        self.export_table(tagwriter)

    def export_table(self, tagwriter: AbstractTagWriter):
        pass

    def __referenced_blocks__(self) -> Iterable[str]:
        """Support for "ReferencedBlocks" protocol."""
        if self.doc:
            block_record_handle = self.dxf.get("block_record_handle", None)
            if block_record_handle:
                return (block_record_handle,)
        return tuple()


acdb_table_style = DefSubclass(
    "AcDbTableStyle",
    {
        # Table style version: 0 = 2010
        "version": DXFAttr(280),
        # Table style description (string; 255 characters maximum):
        "name": DXFAttr(3),
        # FlowDirection (integer):
        # 0 = Down
        # 1 = Up
        "flow_direction": DXFAttr(70),
        # Flags (bit-coded)
        "flags": DXFAttr(71),
        # Horizontal cell margin (real; default = 0.06)
        "horizontal_cell_margin": DXFAttr(40),
        # Vertical cell margin (real; default = 0.06)
        "vertical_cell_margin": DXFAttr(41),
        # Flag for whether the title is suppressed:
        # 0/1 = not suppressed/suppressed
        "suppress_title": DXFAttr(280),
        # Flag for whether the column heading is suppressed:
        # 0/1 = not suppressed/suppressed
        "suppress_column_header": DXFAttr(281),
        # The following group codes are repeated for every cell in the table
        #   7: Text style name (string; default = STANDARD)
        # 140: Text height (real)
        # 170: Cell alignment (integer)
        #  62: Text color (integer; default = BYBLOCK)
        #  63: Cell fill color (integer; default = 7)
        # 283: Flag for whether background color is enabled (default = 0):
        #      0/1 = disabled/enabled
        #  90: Cell data type
        #  91: Cell unit type
        # 274-279: Lineweight associated with each border type of the cell
        #          (default = kLnWtByBlock)
        # 284-289: Flag for visibility associated with each border type of the cell
        #          (default = 1): 0/1 = Invisible/Visible
        # 64-69: Color value associated with each border type of the cell
        #        (default = BYBLOCK)
    },
)


@factory.register_entity
class TableStyle(DXFObject):
    """DXF TABLESTYLE entity

    Every ACAD_TABLE has its own table style.

    Requires DXF version AC1021/R2007
    """

    DXFTYPE = "TABLESTYLE"
    DXFATTRIBS = DXFAttributes(base_class, acdb_table_style)
    MIN_DXF_VERSION_FOR_EXPORT = const.DXF2007

    def __init__(self) -> None:
        super().__init__()
        self.data: Optional[TableStyleData] = None

    def copy_data(self, entity: Self, copy_strategy=default_copy) -> None:
        assert isinstance(entity, TableStyle)
        entity.data = copy.deepcopy(self.data)

    def load_dxf_attribs(
        self, processor: Optional[SubclassProcessor] = None
    ) -> DXFNamespace:
        dxf = super().load_dxf_attribs(processor)
        if processor:
            tags = processor.subclass_by_index(1)
            if tags is None:
                raise const.DXFStructureError(
                    f"Missing subclass AcDbTableStyle in TABLESTYLE(#{dxf.handle})"
                )
            start = 1 if len(tags) and tags[0].code == 100 else 0
            index = start
            if index < len(tags) and tags[index].code == 280:
                dxf.version = int(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == 3:
                dxf.name = str(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == 70:
                dxf.flow_direction = int(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == 71:
                dxf.flags = int(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == 40:
                dxf.horizontal_cell_margin = float(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == 41:
                dxf.vertical_cell_margin = float(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == 280:
                dxf.suppress_title = int(tags[index].value)
                index += 1
            if index < len(tags) and tags[index].code == 281:
                dxf.suppress_column_header = int(tags[index].value)
            self.data = _parse_table_style(tags)
        return dxf

    @property
    def title_style(self) -> Optional[TableStyleCellStyle]:
        return self.data.title_style if self.data is not None else None

    @property
    def header_style(self) -> Optional[TableStyleCellStyle]:
        return self.data.header_style if self.data is not None else None

    @property
    def data_style(self) -> Optional[TableStyleCellStyle]:
        return self.data.data_style if self.data is not None else None


class TableStyleManager(ObjectCollection[TableStyle]):
    def __init__(self, doc: Drawing):
        super().__init__(doc, dict_name="ACAD_TABLESTYLE", object_type="TABLESTYLE")


@factory.register_entity
class TableContent(DXFTagStorage):
    DXFTYPE = "TABLECONTENT"

    def __init__(self) -> None:
        super().__init__()
        self.linked_data: Optional[AcadTableLinkedData] = None

    def load_dxf_attribs(
        self, processor: Optional[SubclassProcessor] = None
    ) -> DXFNamespace:
        dxf = super().load_dxf_attribs(processor)
        if processor:
            tags = processor.subclass_by_index(2)
            if tags is not None:
                self.linked_data = AcadTableLinkedData.from_tags(tags)
        return dxf

    def rows(self) -> list[list[AcadTableLinkedCell]]:
        if self.linked_data is None:
            return []
        return self.linked_data.rows()

    def get_cell(self, row: int, col: int) -> AcadTableLinkedCell:
        if self.linked_data is None:
            raise IndexError("TABLECONTENT has no parsed cell data")
        index = row * max(self.linked_data.n_cols, 1) + col
        return self.linked_data.cells[index]


@factory.register_entity
class AcadTableBlockContent(DXFTagStorage):
    DXFTYPE = "ACAD_TABLE"
    DXFATTRIBS = DXFAttributes(
        base_class, acdb_entity, acdb_block_reference, acdb_table
    )

    def __init__(self) -> None:
        super().__init__()
        self.data: Optional[AcadTableData] = None
        self.linked_data: Optional[AcadTableLinkedData] = None

    def load_dxf_attribs(
        self, processor: Optional[SubclassProcessor] = None
    ) -> DXFNamespace:
        dxf = super().load_dxf_attribs(processor)
        if processor:
            processor.fast_load_dxfattribs(
                dxf, acdb_block_reference_group_codes, subclass=2
            )
            tags = processor.subclass_by_index(3)
            if tags is not None:
                self.data = _parse_acad_table_content(dxf, tags)
        return dxf

    def rows(self) -> list[list[AcadTableCell]]:
        if self.data is None:
            return []
        return self.data.rows()

    def get_cell(self, row: int, col: int) -> AcadTableCell:
        self.load_linked_data()
        if self.data is None:
            raise IndexError("ACAD_TABLE has no parsed cell data")
        index = row * max(self.data.n_cols, 1) + col
        return self.data.cells[index]

    def get_cell_block_name(self, row: int, col: int) -> str:
        cell = self.get_cell(row, col)
        handle = cell.block_record_handle
        if handle is None or self.doc is None:
            return ""
        block_record = self.doc.entitydb.get(handle)
        if block_record is None:
            return ""
        return block_record.dxf.get("name", "")

    def get_cell_block_attribs(self, row: int, col: int) -> dict[str, str]:
        cell = self.get_cell(row, col)
        return self.resolve_block_attribute_tags(cell)

    def get_cell_field(self, row: int, col: int):
        from .dxfobj import Field

        cell = self.get_cell(row, col)
        handle = cell.field_handle
        if handle is None or self.doc is None:
            return None
        field = self.doc.entitydb.get(handle)
        return field if isinstance(field, Field) and field.is_alive else None

    def get_cell_primary_field(self, row: int, col: int):
        field = self.get_cell_field(row, col)
        if field is None:
            return None
        child_fields = field.get_child_fields()
        if field.is_text_wrapper and len(child_fields):
            return child_fields[0]
        return field

    def resolve_block_attribute_tags(self, cell: AcadTableCell) -> dict[str, str]:
        if self.doc is None or not cell.block_attributes:
            return {}
        result: dict[str, str] = {}
        for attrib in cell.block_attributes:
            entity = self.doc.entitydb.get(attrib.handle)
            if entity is None:
                continue
            tag = entity.dxf.get("tag")
            if isinstance(tag, str) and len(tag):
                result[tag] = attrib.text
        return result

    def get_linked_table_content_handle(self) -> Optional[str]:
        if not self.has_extension_dict or self.doc is None:
            return None
        try:
            xdict = self.get_extension_dict()
        except AttributeError:
            return None
        if not xdict.has_valid_dictionary:
            return None
        xrecord = xdict.dictionary.get("ACAD_XREC_ROUNDTRIP")
        if xrecord is None:
            return None
        tags = getattr(xrecord, "tags", None)
        if tags is None:
            return None
        for tag in tags:
            if tag.code == 360:
                return str(tag.value)
        return None

    def get_linked_table_content(self) -> Optional[DXFTagStorage]:
        if self.doc is None:
            return None
        handle = self.get_linked_table_content_handle()
        if handle is None:
            return None
        entity = self.doc.entitydb.get(handle)
        if isinstance(entity, DXFTagStorage) and entity.dxftype() == "TABLECONTENT":
            return entity
        return None

    def load_linked_data(self) -> Optional[AcadTableLinkedData]:
        if self.linked_data is not None:
            return self.linked_data
        table_content = self.get_linked_table_content()
        if table_content is None:
            return None
        if isinstance(table_content, TableContent) and table_content.linked_data is not None:
            self.linked_data = table_content.linked_data
            if self.data is not None and self.linked_data.n_rows == 0:
                self.linked_data.n_rows = self.data.n_rows
                self.linked_data.n_cols = self.data.n_cols
            self._merge_linked_data()
            return self.linked_data
        try:
            tags = table_content.xtags.get_subclass("AcDbLinkedTableData")
        except const.DXFKeyError:
            return None
        n_rows = self.data.n_rows if self.data is not None else 0
        n_cols = self.data.n_cols if self.data is not None else 0
        self.linked_data = AcadTableLinkedData.from_tags(tags, n_rows=n_rows, n_cols=n_cols)
        self._merge_linked_data()
        return self.linked_data

    def _merge_linked_data(self) -> None:
        if self.data is None or self.linked_data is None:
            return
        for linked_cell in self.linked_data.cells:
            index = linked_cell.row * max(self.data.n_cols, 1) + linked_cell.col
            if index >= len(self.data.cells):
                continue
            cell = self.data.cells[index]
            cell.linked_cell_contents = linked_cell.contents
            for content in linked_cell.contents:
                if content.is_block_content:
                    if content.block_record_handle is not None:
                        cell.block_record_handle = content.block_record_handle
                    if content.block_scale is not None:
                        cell.block_scale = content.block_scale
                    if content.alignment is not None:
                        cell.alignment = content.alignment
                    if content.block_attributes:
                        cell.block_attributes = content.block_attributes

    def proxy_graphic_content(self) -> Iterable[DXFGraphic]:
        return super().__virtual_entities__()

    def _block_content(self) -> Iterator[DXFGraphic]:
        block_name: str = self.get_block_name()
        return self.doc.blocks.get(block_name, [])  # type: ignore

    def get_block_name(self) -> str:
        return self.dxf.get("geometry", "")

    def get_insert_location(self) -> Vec3:
        return self.dxf.get("insert", Vec3())

    def __virtual_entities__(self) -> Iterator[DXFGraphic]:
        """Implements the SupportsVirtualEntities protocol."""
        insert: Vec3 = Vec3(self.get_insert_location())
        m: Optional[Matrix44] = None
        if insert:
            # TODO: OCS transformation (extrusion) is ignored yet
            m = Matrix44.translate(insert.x, insert.y, insert.z)

        for entity in self._block_content():
            try:
                clone = entity.copy()
            except const.DXFTypeError:
                continue
            if m is not None:
                try:
                    clone.transform(m)
                except:  # skip entity at any transformation issue
                    continue
            yield clone


def acad_table_to_block(table: DXFEntity) -> None:
    """Converts the given ACAD_TABLE entity to a block references (INSERT entity).

    The original ACAD_TABLE entity will be destroyed.

    .. versionadded:: 1.1

    """
    if not isinstance(table, AcadTableBlockContent):
        return
    doc = table.doc
    owner = table.dxf.owner
    block_name = table.get_block_name()
    if doc is None or block_name == "" or owner is None:
        return
    try:
        layout = doc.layouts.get_layout_by_key(owner)
    except const.DXFKeyError:
        return
    # replace ACAD_TABLE entity by INSERT entity
    layout.add_blockref(
        block_name,
        insert=table.get_insert_location(),
        dxfattribs={"layer": table.dxf.get("layer", "0")},
    )
    layout.delete_entity(table)  # type: ignore


def read_acad_table_content(table: DXFTagStorage) -> list[list[str]]:
    """Returns the content of an ACAD_TABLE entity as list of table rows.

    If the count of table rows or table columns is missing the complete content is
    stored in the first row.
    """
    if table.dxftype() != "ACAD_TABLE":
        raise const.DXFTypeError(f"Expected ACAD_TABLE entity, got {str(table)}")
    data = getattr(table, "data", None)
    if isinstance(data, AcadTableData):
        return data.text_content()
    acdb_table = table.xtags.get_subclass("AcDbTable")

    nrows = acdb_table.get_first_value(91, 0)
    ncols = acdb_table.get_first_value(92, 0)
    split_code = 171  # DXF R2004
    if acdb_table.has_tag(302):
        split_code = 301  # DXF R2007 and later
    values = _load_table_values(acdb_table, split_code)
    if nrows * ncols == 0:
        return [values]
    content: list[list[str]] = []
    for index in range(nrows):
        start = index * ncols
        content.append(values[start : start + ncols])
    return content


def _load_table_values(tags: Tags, split_code: int) -> list[str]:
    values: list[str] = []
    for group in group_tags(tags, splitcode=split_code):
        g_tags = Tags(group)
        if g_tags.has_tag(302):  # DXF R2007 and later
            # contains all text as one long string, with more than 66000 chars tested
            values.append(g_tags.get_first_value(302))
        else:  
            # DXF R2004
            # Text is divided into chunks (2, 2, 2, ..., 1) or (3, 3, 3, ..., 1)
            # DXF reference says group code 2, BricsCAD writes group code 3
            s = "".join(tag.value for tag in g_tags if 1 <= tag.code <= 3)
            values.append(s)
    return values
