# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
import ezdxf

from ezdxf.entities.acad_table import (
    AcadTableBlockAttributeValue,
    AcadTableBlockContent,
    AcadTableCell,
    AcadTableData,
    AcadTableLinkedData,
    TableContent,
    TableStyle,
    read_acad_table_content,
)
from ezdxf.lldxf.tags import Tags


def make_table(cell1: str, cell2: str, cell3: str, first_cell_extra: str = "", row1: str = "11.0") -> str:
    return f"""0
ACAD_TABLE
5
1
330
0
100
AcDbEntity
8
0
100
AcDbBlockReference
2
*T0
10
0.0
20
0.0
30
0.0
100
AcDbTable
280
0
342
4C
343
69
11
1.0
21
0.0
31
0.0
90
22
91
3
92
1
93
0
94
0
95
0
96
0
141
{row1}
141
9.0
141
9.0
142
63.5
171
1
172
0
173
0
174
0
175
1
176
1
91
262144
178
0
145
0.0
{first_cell_extra}92
0
301
CELL_VALUE
93
6
90
4
1
{cell1}
94
0
300

302
{cell1}
304
ACVALUE_END
171
1
172
0
173
0
174
0
175
1
176
1
91
262144
178
0
145
0.0
92
0
301
CELL_VALUE
93
6
90
4
1
{cell2}
94
0
300

302
{cell2}
304
ACVALUE_END
171
1
172
0
173
0
174
0
175
1
176
1
91
262144
178
0
145
0.0
92
0
301
CELL_VALUE
93
6
90
4
1
{cell3}
94
0
300

302
{cell3}
304
ACVALUE_END
"""


TEXT_TABLE = make_table("T", "H", "D")

HEIGHT_OVERRIDE_TABLE = make_table(
    "T",
    "H",
    "D",
    first_cell_extra="140\n20.0\n",
    row1="29.66666666666667",
).replace("262144\n178", "262176\n178", 1)

ALIGNMENT_OVERRIDE_TABLE = make_table(
    "T",
    "H",
    "D",
    first_cell_extra="170\n4\n",
).replace("262144\n178", "262145\n178", 1)

INLINE_COLOR_TABLE = make_table(r"{\C215;\c10507177;T}", "H", "D")

BLOCK_CELL_TABLE = """0
ACAD_TABLE
5
1
330
0
100
AcDbEntity
8
0
100
AcDbBlockReference
2
*T0
10
0.0
20
0.0
30
0.0
100
AcDbTable
280
0
342
4C
343
69
11
1.0
21
0.0
31
0.0
90
22
91
3
92
1
93
0
94
0
95
0
96
0
141
11.0
141
9.0
141
9.0
142
63.5
171
1
172
0
173
0
174
0
175
1
176
1
91
262144
178
0
145
0.0
92
0
301
CELL_VALUE
93
6
90
4
1
T
94
0
300

302
T
304
ACVALUE_END
171
1
172
0
173
0
174
0
175
1
176
1
91
262144
178
0
145
0.0
92
0
301
CELL_VALUE
93
6
90
4
1
H
94
0
300

302
H
304
ACVALUE_END
171
2
172
0
173
0
174
0
175
1
176
1
91
262145
178
0
145
0.0
340
91
144
1.0
179
0
170
1
92
0
301
CELL_VALUE
93
1
90
4
94
0
300

302

304
ACVALUE_END
"""


TABLESTYLE_TEXT = """0
TABLESTYLE
5
4C
330
15
100
AcDbTableStyle
280
0
3
Standard
70
0
71
0
40
1.5
41
1.5
280
0
281
0
7
Standard
140
4.5
170
2
62
0
63
7
283
0
90
512
91
0
1

274
-2
284
1
64
0
275
-2
285
1
65
0
276
-2
286
1
66
0
277
-2
287
1
67
0
278
-2
288
1
68
0
279
-2
289
1
69
0
7
Standard
140
6.0
170
5
62
0
63
7
283
0
90
512
91
0
1

274
-2
284
1
64
0
275
-2
285
1
65
0
276
-2
286
1
66
0
277
-2
287
1
67
0
278
-2
288
1
68
0
279
-2
289
1
69
0
7
Standard
140
4.5
170
5
62
0
63
7
283
0
90
512
91
0
1

274
-2
284
1
64
0
275
-2
285
1
65
0
276
-2
286
1
66
0
277
-2
287
1
67
0
278
-2
288
1
68
0
279
-2
289
1
69
0
"""


LINKED_BLOCK_CELL_TAGS = Tags.from_text(
    """100
AcDbLinkedTableData
1
LINKEDTABLEDATACELL_BEGIN
302
CONTENT
1
CELLCONTENT_BEGIN
90
4
340
2F
91
2
330
34
301
X
92
1
330
35
301
Y
92
2
309
CELLCONTENT_END
309
LINKEDTABLEDATACELL_END
"""
)


TABLECONTENT_TEXT = """0
TABLECONTENT
5
9E
330
A1
100
AcDbLinkedData
1

300

100
AcDbLinkedTableData
90
1
1
LINKEDTABLEDATACELL_BEGIN
302
CONTENT
1
CELLCONTENT_BEGIN
90
4
340
2F
91
2
330
34
301
X
92
1
330
35
301
Y
92
2
309
CELLCONTENT_END
309
LINKEDTABLEDATACELL_END
"""


def load_table(text: str) -> AcadTableBlockContent:
    return AcadTableBlockContent.from_text(text)


def test_reads_minimal_text_table_structure():
    table = load_table(TEXT_TABLE)

    assert table.dxf.n_rows == 3
    assert table.dxf.n_cols == 1
    assert table.data is not None
    assert table.data.row_heights == [11.0, 9.0, 9.0]
    assert table.data.col_widths == [63.5]
    assert read_acad_table_content(table) == [["T"], ["H"], ["D"]]


def test_reads_cell_text_height_override():
    table = load_table(HEIGHT_OVERRIDE_TABLE)
    cell = table.get_cell(0, 0)

    assert table.data is not None
    assert table.data.row_heights[0] == 29.66666666666667
    assert cell.override_flags == 262176
    assert cell.text_height == 20.0


def test_reads_cell_alignment_override():
    table = load_table(ALIGNMENT_OVERRIDE_TABLE)
    cell = table.get_cell(0, 0)

    assert cell.override_flags == 262145
    assert cell.alignment == 4


def test_preserves_inline_content_color_codes_in_text_payload():
    table = load_table(INLINE_COLOR_TABLE)
    cell = table.get_cell(0, 0)

    assert cell.override_flags == 262144
    assert cell.text == r"{\C215;\c10507177;T}"


def test_reads_minimal_block_cell_structure():
    table = load_table(BLOCK_CELL_TABLE)
    cell = table.get_cell(2, 0)

    assert cell.is_block_cell is True
    assert cell.override_flags == 262145
    assert cell.block_record_handle == "91"
    assert cell.block_scale == 1.0
    assert cell.block_attribute_count == 0
    assert cell.alignment == 1
    assert cell.text == ""


def test_parses_linked_block_cell_attribute_payload():
    linked = AcadTableLinkedData.from_tags(LINKED_BLOCK_CELL_TAGS, n_rows=1, n_cols=1)
    cell = linked.cells[0]
    content = cell.contents[0]

    assert cell.row == 0
    assert cell.col == 0
    assert content.content_type == 4
    assert content.block_record_handle == "2F"
    assert len(content.block_attributes) == 2
    assert content.block_attributes[0].handle == "34"
    assert content.block_attributes[0].text == "X"
    assert content.block_attributes[0].index == 1
    assert content.block_attributes[1].handle == "35"
    assert content.block_attributes[1].text == "Y"
    assert content.block_attributes[1].index == 2


def test_merges_linked_block_cell_attributes_into_table_cell():
    table = load_table(BLOCK_CELL_TABLE)
    assert table.data is not None
    table.linked_data = AcadTableLinkedData.from_tags(
        LINKED_BLOCK_CELL_TAGS, n_rows=table.data.n_rows, n_cols=table.data.n_cols
    )
    table.linked_data.cells[0].row = 2
    table.linked_data.cells[0].col = 0

    table._merge_linked_data()
    cell = table.get_cell(2, 0)

    assert len(cell.linked_cell_contents) == 1
    assert cell.block_record_handle == "2F"
    assert len(cell.block_attributes) == 2
    assert cell.block_attributes[0].text == "X"
    assert cell.block_attributes[1].text == "Y"


def test_resolves_block_attribute_tag_names_and_values():
    doc = ezdxf.new("R2018")
    block = doc.blocks.new("TABLE_BLOCK_CELL_ATTRIB")
    attdef1 = block.add_attdef("TAG1", insert=(0, 0), text="A")
    attdef2 = block.add_attdef("TAG2", insert=(1, 1), text="B")
    table = AcadTableBlockContent.new(doc=doc)
    table.data = AcadTableData(
        n_rows=1,
        n_cols=1,
        cells=[
            AcadTableCell(
                row=0,
                col=0,
                cell_type=2,
                block_record_handle=block.block_record_handle,
                block_attributes=[],
            )
        ],
    )
    cell = table.get_cell(0, 0)
    cell.block_attributes = [
        AcadTableBlockAttributeValue(attdef1.dxf.handle, "X", 1),
        AcadTableBlockAttributeValue(attdef2.dxf.handle, "Y", 2),
    ]

    assert table.get_cell_block_name(0, 0) == "TABLE_BLOCK_CELL_ATTRIB"
    assert table.get_cell_block_attribs(0, 0) == {"TAG1": "X", "TAG2": "Y"}


def test_resolves_direct_cell_field_handle():
    doc = ezdxf.new("R2018")
    field = doc.objects.add_field(owner="0")
    field.set_acvar("Author", display="----")
    table = AcadTableBlockContent.from_text(
        make_table("T", "H", "D", first_cell_extra=f"344\n{field.dxf.handle}\n"),
        doc=doc,
    )

    assert table.get_cell(0, 0).field_handle == field.dxf.handle
    assert table.get_cell_field(0, 0) is field
    assert table.get_cell_primary_field(0, 0) is field


def test_resolves_wrapped_cell_field_to_primary_child():
    doc = ezdxf.new("R2018")
    child = doc.objects.add_field(owner="0")
    child.set_acvar("Author", display="----")
    wrapper = doc.objects.add_field(owner="0")
    wrapper.set_text_wrapper(child, text="----")
    child.dxf.owner = wrapper.dxf.handle

    table = AcadTableBlockContent.from_text(
        make_table("T", "H", "D", first_cell_extra=f"344\n{wrapper.dxf.handle}\n"),
        doc=doc,
    )

    assert table.get_cell_field(0, 0) is wrapper
    assert table.get_cell_primary_field(0, 0) is child


def test_reads_table_style_cell_buckets():
    style = TableStyle.from_text(TABLESTYLE_TEXT)

    assert style.dxf.name == "Standard"
    assert style.dxf.flow_direction == 0
    assert style.dxf.flags == 0
    assert style.dxf.horizontal_cell_margin == 1.5
    assert style.dxf.vertical_cell_margin == 1.5
    assert style.data is not None
    assert len(style.data.cell_styles) == 3
    assert style.title_style is not None
    assert style.title_style.text_style == "Standard"
    assert style.title_style.text_height == 4.5
    assert style.title_style.alignment == 2
    assert style.header_style is not None
    assert style.header_style.text_height == 6.0
    assert style.header_style.alignment == 5
    assert style.data_style is not None
    assert style.data_style.text_height == 4.5
    assert style.data_style.alignment == 5


def test_document_exposes_table_style_manager():
    doc = ezdxf.new("R2018")

    assert doc.table_styles is not None
    assert doc.table_styles.object_type == "TABLESTYLE"


def test_tablecontent_loads_linked_table_data():
    content = TableContent.from_text(TABLECONTENT_TEXT)

    assert content.linked_data is not None
    assert len(content.linked_data.cells) == 1
    linked_cell = content.linked_data.cells[0]
    assert len(linked_cell.contents) == 1
    assert linked_cell.contents[0].block_attributes[0].text == "X"
    assert linked_cell.contents[0].block_attributes[1].text == "Y"


def test_acad_table_uses_typed_tablecontent_when_available(monkeypatch):
    table = load_table(BLOCK_CELL_TABLE)
    table_content = TableContent.from_text(TABLECONTENT_TEXT)
    monkeypatch.setattr(table, "get_linked_table_content", lambda: table_content)

    linked = table.load_linked_data()

    assert linked is not None
    assert linked is table_content.linked_data
