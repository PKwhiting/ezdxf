# Procedure

## Goal

Establish the smallest useful `ACAD_TABLE` DXF diffs authored by AutoCAD, so the
current preservation-only support in `ezdxf` can be expanded from real
observations instead of incomplete DXF reference material.

## Seed Artifact

- Baseline generator:
  - `experiments/acad-table-diffs/generate_acad_table_seed.py`
- Baseline DXF:
  - `experiments/acad-table-diffs/acad_table_seed.dxf`

Regenerate the seed at any time by running the generator script.

## Suggested Manual Workflow

1. Open `acad_table_seed.dxf` in AutoCAD.
2. Add exactly one controlled `ACAD_TABLE` variant.
3. Save the result as a new file in `experiments/acad-table-diffs/`.
4. Diff the baseline DXF against the edited DXF.
5. Save the edited DXF a second time and diff first-save vs second-save output
   to separate authoring structure from AutoCAD canonicalization noise.

## First Variants

### Variant 1

- 1 row x 1 column
- text cell only
- short ASCII text
- default `TABLESTYLE`

Questions:

- Which top-level `AcDbTable` tags appear first?
- Where are row count, column count, row height, and column width stored?
- Which tag sequence defines a single text cell value?

### Variant 2

- 2 rows x 2 columns
- text cells only
- distinct short values per cell
- default `TABLESTYLE`

Questions:

- What is the cell ordering in the tag stream?
- Are cell records grouped row-major?
- Which tags repeat once per row, once per column, and once per cell?

### Variant 3

- same table as Variant 2
- change one thing only:
  - alignment, or
  - text height, or
  - background fill, or
  - one border visibility/color

Questions:

- Which tags represent overrides?
- Are overrides table-wide, row-type based, or truly cell-local?

## Follow-up Variants

- long text cell content
- empty cells
- merged cells
- custom `TABLESTYLE`
- block cell content
- fields in text cells
- block cells with attributes

## Current Known Limits in `ezdxf`

- `src/ezdxf/entities/acad_table.py`
  - `AcadTable.load_table()` is unimplemented
  - `AcadTable.export_table()` is unimplemented
  - `TableStyle` is marked TODO
- Runtime behavior is currently centered on preservation helpers:
  - `read_acad_table_content(...)`
  - `acad_table_to_block(...)`
  - `AcadTableBlockContent`

## Notes

- Change one thing per file.
- Prefer short ASCII text first.
- Keep variant names descriptive, for example:
  - `acad_table_001_1x1_text_default.dxf`
  - `acad_table_002_2x2_text_default.dxf`
  - `acad_table_003_2x2_text_alignment_middle_center.dxf`
