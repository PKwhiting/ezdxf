# Procedure

## Goal

Prepare the first focused probe package for authored block-cell support, without
implementing block-cell export yet.

## Starting Point

Use the already validated read-side block-cell baselines:

- `experiments/acad-table-diffs/acad_table_010_true_block_cell_minimal.dxf`
- `experiments/acad-table-diffs/acad_table_011_true_block_cell_with_attribs.dxf`

## Suggested Next Probe Work

1. Build a minimal `ezdxf`-authored table shell with one block cell in the data
   row.
2. Start from the smallest semantic shell fields already confirmed for block
   cells:
   - `171 = 2`
   - `340 = <block-record-handle>`
   - `144 = 1.0`
   - `170 = <alignment>`
3. Test variants with and without linked `TABLECONTENT`.
4. Roundtrip each variant through AutoCAD Core Console.
5. Compare accepted variants against the existing AutoCAD-authored baselines.

## Questions

- Is a minimal block-cell authoring path possible without linked `TABLECONTENT`?
- Which semantic-shell tags are mandatory for the first accepted block-cell export?
- At what point do ATTDEF-backed values require authored linked `TABLECONTENT`?
