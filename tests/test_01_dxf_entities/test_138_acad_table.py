# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
from ezdxf.entities.acad_table import AcadTableBlockContent, read_acad_table_content


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
