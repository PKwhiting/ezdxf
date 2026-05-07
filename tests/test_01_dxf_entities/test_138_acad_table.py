# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
import ezdxf
import pytest
from ezdxf.lldxf.tagwriter import TagCollector
from ezdxf.lldxf import const

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
from ezdxf.entities import factory
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

LOCAL_TEXT_COLOR_TABLE = make_table(
    "T",
    "H",
    "D",
    first_cell_extra="63\n217\n421\n9643919\n283\n0\n",
).replace("262144\n178", "262150\n178", 1)

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


TABLECONTENT_WRAPPED_TEXT = """0
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
FORMATTEDTABLEDATACOLUMN_BEGIN
300
COLUMNTABLEFORMAT
1
TABLEFORMAT_BEGIN
90
3
170
0
309
TABLEFORMAT_END
309
FORMATTEDTABLEDATACOLUMN_END
1
TABLECOLUMN_BEGIN
90
0
40
63.5
309
TABLECOLUMN_END
1
LINKEDTABLEDATACELL_BEGIN
302
CONTENT
1
CELLCONTENT_BEGIN
90
1
300
VALUE
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
91
0
309
CELLCONTENT_END
309
LINKEDTABLEDATACELL_END
1
FORMATTEDTABLEDATACELL_BEGIN
300
CELLTABLEFORMAT
1
TABLEFORMAT_BEGIN
90
1
170
1
91
0
92
0
62
257
93
1
300
CONTENTFORMAT
1
CONTENTFORMAT_BEGIN
90
0
91
0
92
512
93
0
300

40
0.0
140
1.0
94
5
62
0
340
0
144
0.18
309
CONTENTFORMAT_END
171
0
94
0
309
TABLEFORMAT_END
309
FORMATTEDTABLEDATACELL_END
1
TABLECELL_BEGIN
90
0
91
0
309
TABLECELL_END
1
FORMATTEDTABLEDATAROW_BEGIN
300
ROWTABLEFORMAT
1
TABLEFORMAT_BEGIN
90
2
170
0
309
TABLEFORMAT_END
309
FORMATTEDTABLEDATAROW_END
1
TABLEROW_BEGIN
90
0
40
11.0
309
TABLEROW_END
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


def test_reads_local_text_color_override_tags():
    table = load_table(LOCAL_TEXT_COLOR_TABLE)
    cell = table.get_cell(0, 0)

    assert cell.override_flags == 262150
    assert cell.fill_color == 217
    assert cell.fill_true_color == 9643919
    assert cell.fill_enabled == 0


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


def test_modelspace_add_table_creates_text_only_acad_table():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table((1, 2), [["T"], ["H"], ["D"]])

    assert table.dxftype() == "ACAD_TABLE"
    assert table.dxf.insert == (1, 2, 0)
    assert table.data is not None
    assert table.data.row_heights == [11.0, 9.0, 9.0]
    assert table.data.col_widths == [63.5]
    assert read_acad_table_content(table) == [["T"], ["H"], ["D"]]
    assert table.get_table_style() is doc.table_styles.get("Standard")
    assert table.dxf.geometry.startswith("*T")
    assert not table.has_extension_dict
    assert table.load_linked_data() is None

    entity_types = [entity.dxftype() for entity in table.virtual_entities()]
    assert entity_types.count("LINE") == 6
    assert entity_types.count("MTEXT") == 3


def test_exports_created_text_only_acad_table():
    doc = ezdxf.new("R2018")
    style = doc.table_styles.get("Standard")
    table = doc.modelspace().add_table((0, 0), [["T"], ["H"], ["D"]])

    assert style is not None

    collector = TagCollector(dxfversion=doc.dxfversion)
    table.export_dxf(collector)
    exported = Tags(collector.tags)

    assert exported.get_first_value(0) == "ACAD_TABLE"
    assert exported.get_first_value(2).startswith("*T")
    assert exported.get_first_value(342) == style.dxf.handle
    assert [tag.value for tag in exported.find_all(141)] == [11.0, 9.0, 9.0]
    assert [tag.value for tag in exported.find_all(142)] == [63.5]
    assert [tag.value for tag in exported.find_all(302)] == ["T", "H", "D"]


def test_add_table_requires_dxf_r2007():
    doc = ezdxf.new("R2004")

    with pytest.raises(const.DXFVersionError):
        doc.modelspace().add_table((0, 0), [["D"]])


def test_add_table_two_rows_suppresses_title_and_keeps_explicit_sizes():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table(
        (0, 0),
        [["H1", "H2"], ["D1", "D2"]],
        row_heights=[9.0, 10.5],
        col_widths=[20.0, 30.0],
    )

    assert table.data is not None
    assert table.data.suppress_title == 1
    assert table.data.suppress_column_header == 0
    assert table.data.row_heights == [9.0, 10.5]
    assert table.data.col_widths == [20.0, 30.0]
    assert read_acad_table_content(table) == [["H1", "H2"], ["D1", "D2"]]


def test_add_table_one_row_suppresses_title_and_header():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table((0, 0), [["D1", "D2", "D3"]])

    assert table.data is not None
    assert table.data.suppress_title == 1
    assert table.data.suppress_column_header == 1
    assert table.data.row_heights == [9.0]
    assert read_acad_table_content(table) == [["D1", "D2", "D3"]]


def test_exports_authored_text_height_override_and_uses_it_for_geometry():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table((0, 0), [["T"], ["H"], ["D"]])
    assert table.data is not None
    table.data.row_heights[0] = 29.66666666666667
    table.set_cell_text_height(0, 0, 20.0)

    collector = TagCollector(dxfversion=doc.dxfversion)
    table.export_dxf(collector)
    exported = Tags(collector.tags)

    assert exported.find_all(140)[0].value == 20.0
    assert exported.find_all(91)[1].value == 262176

    block = doc.blocks.get(table.dxf.geometry)
    assert block is not None
    mtext = list(block.query("MTEXT"))[0]
    assert mtext.dxf.char_height == 20.0


def test_exports_authored_alignment_override_and_uses_it_for_geometry():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table((0, 0), [["T"], ["H"], ["D"]])
    table.set_cell_alignment(0, 0, 4)

    collector = TagCollector(dxfversion=doc.dxfversion)
    table.export_dxf(collector)
    exported = Tags(collector.tags)

    assert exported.find_all(170)[0].value == 4
    assert exported.find_all(91)[1].value == 262145

    block = doc.blocks.get(table.dxf.geometry)
    assert block is not None
    mtext = list(block.query("MTEXT"))[0]
    assert mtext.dxf.attachment_point == 4
    assert mtext.dxf.insert == (1.5, -5.5, 0.0)


def test_exports_authored_inline_content_color_and_rebuilds_geometry():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table((0, 0), [["T"], ["H"], ["D"]])
    table.set_cell_content_color(0, 0, 215, 10507177)

    collector = TagCollector(dxfversion=doc.dxfversion)
    table.export_dxf(collector)
    exported = Tags(collector.tags)

    assert exported.find_all(91)[1].value == 262144
    assert exported.find_all(1)[0].value == r"{\C215;\c10507177;T}"
    assert exported.find_all(302)[0].value == r"{\C215;\c10507177;T}"

    block = doc.blocks.get(table.dxf.geometry)
    assert block is not None
    mtext = list(block.query("MTEXT"))[0]
    assert mtext.text == r"{\C215;\c10507177;T}"


def test_set_cell_text_updates_export_and_geometry():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table((0, 0), [["T"], ["H"], ["D"]])
    table.set_cell_text(0, 0, "TITLE-LONG")

    collector = TagCollector(dxfversion=doc.dxfversion)
    table.export_dxf(collector)
    exported = Tags(collector.tags)

    assert exported.find_all(1)[0].value == "TITLE-LONG"
    assert exported.find_all(302)[0].value == "TITLE-LONG"

    block = doc.blocks.get(table.dxf.geometry)
    assert block is not None
    mtext = list(block.query("MTEXT"))[0]
    assert mtext.text == "TITLE-LONG"


def test_exports_authored_local_text_color_override_and_rebuilds_geometry():
    doc = ezdxf.new("R2018")
    table = doc.modelspace().add_table((0, 0), [["T"], ["H"], ["D"]])
    table.set_cell_text_color(0, 0, 217, 9643919)

    collector = TagCollector(dxfversion=doc.dxfversion)
    table.export_dxf(collector)
    exported = Tags(collector.tags)

    assert exported.find_all(91)[1].value == 262150
    assert exported.find_all(63)[0].value == 217
    assert exported.find_all(421)[0].value == 9643919
    assert exported.find_all(283)[0].value == 0

    block = doc.blocks.get(table.dxf.geometry)
    assert block is not None
    mtext = list(block.query("MTEXT"))[0]
    assert mtext.dxf.color == 217
    assert mtext.dxf.true_color == 9643919


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
    standard = doc.table_styles.get("Standard")
    assert standard is not None
    assert standard.data is not None
    assert standard.title_style is not None


def test_exports_created_standard_table_style():
    doc = ezdxf.new("R2018")
    style = doc.table_styles.get("Standard")

    assert style is not None
    assert style.data is not None

    collector = TagCollector(dxfversion=doc.dxfversion)
    style.export_dxf(collector)
    exported = Tags(collector.tags)

    assert exported.get_first_value(0) == "TABLESTYLE"
    assert exported.find_all(7)[0].value == "Standard"
    heights = [tag.value for tag in exported.find_all(140)]
    assert heights[:3] == [4.5, 6.0, 4.5]


def bind_object(doc, entity):
    factory.bind(entity, doc)
    doc.objects.add_object(entity)
    return entity


def test_resolves_table_style_and_default_row_buckets():
    doc = ezdxf.new("R2018")
    style = bind_object(doc, TableStyle.from_text(TABLESTYLE_TEXT, doc=doc))
    table = load_table(TEXT_TABLE)
    table.doc = doc
    table.dxf.table_style_id = style.dxf.handle

    assert table.get_table_style() is style
    assert table.get_row_style_bucket(0) is style.title_style
    assert table.get_row_style_bucket(1) is style.header_style
    assert table.get_row_style_bucket(2) is style.data_style
    assert table.get_cell_style_bucket(2, 0) is style.data_style


def test_row_bucket_mapping_respects_suppressed_title():
    doc = ezdxf.new("R2018")
    style = bind_object(doc, TableStyle.from_text(TABLESTYLE_TEXT, doc=doc))
    table = load_table(TEXT_TABLE)
    table.doc = doc
    table.dxf.table_style_id = style.dxf.handle
    assert table.data is not None
    table.data.suppress_title = 1

    assert table.get_row_style_bucket(0) is style.header_style
    assert table.get_row_style_bucket(1) is style.data_style


def test_tablecontent_loads_linked_table_data():
    content = TableContent.from_text(TABLECONTENT_TEXT)

    assert content.linked_data is not None
    assert len(content.linked_data.cells) == 1
    linked_cell = content.linked_data.cells[0]
    assert len(linked_cell.contents) == 1
    assert linked_cell.contents[0].block_attributes[0].text == "X"
    assert linked_cell.contents[0].block_attributes[1].text == "Y"


def test_tablecontent_parses_linked_column_row_and_cell_wrappers():
    content = TableContent.from_text(TABLECONTENT_WRAPPED_TEXT)

    assert content.linked_data is not None
    assert len(content.linked_data.columns) == 1
    assert content.linked_data.columns[0].width == 63.5
    assert content.linked_data.columns[0].table_format is not None
    assert content.linked_data.columns[0].table_format.kind == "COLUMNTABLEFORMAT"
    assert content.linked_data.columns[0].table_format.alignment == 0
    assert len(content.linked_data.rows_meta) == 1
    assert content.linked_data.rows_meta[0].height == 11.0
    assert content.linked_data.rows_meta[0].table_format is not None
    assert content.linked_data.rows_meta[0].table_format.kind == "ROWTABLEFORMAT"
    linked_cell = content.linked_data.cells[0]
    assert linked_cell.table_format is not None
    assert linked_cell.table_format.kind == "CELLTABLEFORMAT"
    assert linked_cell.table_format.content_format is not None
    assert linked_cell.table_format.content_format.text_height == 1.0
    assert linked_cell.raw_table_flags90 == 0
    assert linked_cell.raw_table_flags91 == 0
    assert content.get_column(0).width == 63.5
    assert content.get_row(0).height == 11.0
    assert content.get_cell(0, 0).table_format is not None


def test_acad_table_uses_typed_tablecontent_when_available(monkeypatch):
    table = load_table(BLOCK_CELL_TABLE)
    table_content = TableContent.from_text(TABLECONTENT_TEXT)
    monkeypatch.setattr(table, "get_linked_table_content", lambda: table_content)

    linked = table.load_linked_data()

    assert linked is not None
    assert linked is table_content.linked_data


def test_acad_table_exposes_linked_wrapper_accessors(monkeypatch):
    table = load_table(TEXT_TABLE)
    table_content = TableContent.from_text(TABLECONTENT_WRAPPED_TEXT)
    monkeypatch.setattr(table, "get_linked_table_content", lambda: table_content)

    assert table.get_linked_column(0).width == 63.5
    assert table.get_linked_row(0).height == 11.0
    assert table.get_linked_cell(0, 0).table_format is not None
