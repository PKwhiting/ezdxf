# Findings

## Summary

AutoCAD stores `ACAD_TABLE` as a semantic table entity plus generated block/
cache content. A useful first typed support tier does not need full table-style
 decoding: row/column counts, row heights, column widths, ordered text-cell
 content, and several important cell-local overrides are all readable directly
 from the `AcDbTable` tag stream.

## Confirmed Changes

1. A table created as "1 data row, 1 column" still becomes a semantic 3-row table in DXF: Title, Header, and Data.
2. The main `AcDbTable` shell stores readable top-level counts and dimensions:
   - `91` row count
   - `92` column count
   - repeated `141` row heights
   - repeated `142` column widths
3. Text-cell values are stored readably in the cell records, typically in both group code `1` and group code `302` inside the `CELL_VALUE` payload.
4. Title text-height changes are stored as a local cell override:
   - cell-local override flag `91` changes
   - local `140` stores the explicit height
   - the title row height in the repeated `141` list changes as well
5. Title alignment changes are stored as a local cell override:
   - cell-local override flag `91` changes
   - local `170` stores the alignment value
6. Title content/text color can be stored inline in the text payload itself, e.g. `{"\\C215;\\c10507177;T"}`, without adding a new readable local color tag or changing the override bitmask.
7. A minimal block cell uses a distinct cell type and readable block-cell tags:
   - `171 = 2` for block cell
   - `340` block record handle
   - `144` block scale
   - `170` alignment
8. AutoCAD also creates a generated anonymous geometry block for the visible rendering and writes extra `ACDSDATA` / thumbnail churn, but these are not required to understand the basic semantic table model.
9. Block-cell content with ATTDEF-backed values is not stored only in the simple `AcDbTable` cell shell. AutoCAD also writes a separate `TABLECONTENT` object using `AcDbLinkedTableData`, `LINKEDTABLEDATACELL_BEGIN`, `CELLCONTENT_BEGIN`, and `FORMATTEDCELLCONTENT_BEGIN` records.
10. In that `TABLECONTENT` object, ATTDEF-backed block-cell values are stored readably as repeated handle/value pairs inside `CELLCONTENT_BEGIN`, for example:
    - `340` block record handle
    - repeated `330` ATTDEF handle
    - `301` attribute text value
    - repeated `92` index markers

## Key Excerpts

Minimal role-row table shell:

```text
91
        3
92
        1
141
11.0
141
9.0
141
9.0
142
63.5
```

Text cell payload:

```text
301
CELL_VALUE
93
        6
90
        4
1
T
302
T
304
ACVALUE_END
```

Title text-height override:

```text
91
   262176
140
20.0
```

Title alignment override:

```text
91
   262145
170
        4
```

Title content-color override stored inline:

```text
1
{\C215;\c10507177;T}
302
{\C215;\c10507177;T}
```

Minimal block-cell record:

```text
171
        2
91
   262145
340
91
144
1.0
179
        0
170
        1
```

Block-cell-with-attributes payload from the linked table data object:

```text
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
```

## Interpretation

- The first useful `ACAD_TABLE` MVP is a typed read model layered on top of the existing preservation-first implementation.
- Cell-local override bitmasks are meaningful and should be preserved/exposed even if not fully decoded.
- Not every visual text change becomes a separate DXF tag; inline text formatting has to be preserved as part of the cell text payload.
- The next layer after the MVP is not full `TABLESTYLE` decoding first; it is parsing the linked `TABLECONTENT` objects to expose richer block-cell payloads and formatted cell content.
- A useful adjacent improvement is typed `TABLESTYLE` read support for the three readable style buckets (Title/Header/Data), without attempting full write support.
- That linked table-content layer is valuable enough to justify its own typed `TABLECONTENT` loader, instead of treating it as opaque tag storage.
- Full `TABLESTYLE` and generated geometry decoding can be deferred; they are not prerequisites for basic semantic table access.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `docs/source/tasks/get_entity_content.rst`

## Artifacts

- `experiments/acad-table-diffs/acad_table_002_1col_1data_default_role_rows.dxf`
- `experiments/acad-table-diffs/acad_table_006_true_title_text_height_override.dxf`
- `experiments/acad-table-diffs/acad_table_007_true_title_alignment_override.dxf`
- `experiments/acad-table-diffs/acad_table_009_true_title_content_color_override.dxf`
- `experiments/acad-table-diffs/acad_table_010_true_block_cell_minimal.dxf`

## Non-Goals From This Experiment

- full `ACAD_TABLE` authoring support
- full `TABLESTYLE` semantic decoding
- byte-level reproduction of AutoCAD-generated geometry or `ACDSDATA` caches
