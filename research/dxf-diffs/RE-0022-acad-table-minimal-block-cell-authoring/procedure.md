# Procedure

## Goal

Validate the smallest useful authored block-cell export for `ACAD_TABLE` without
linked `TABLECONTENT` support.

## Authored Shape

1. Create a text-only `ACAD_TABLE` with three rows.
2. Turn the data-row cell into a block cell by:
   - `set_cell_block(row=2, col=0, block_name=..., block_scale=1.0, alignment=1)`
3. Export the semantic shell with:
   - `171 = 2`
   - `91 = 262145`
   - `340 = <block-record-handle>`
   - `144 = 1.0`
   - `179 = 0`
   - `170 = 1`
4. Rebuild the anonymous `*T` geometry block with a visible `INSERT` of the
   target block.
5. Roundtrip the authored validation sheet through AutoCAD Core Console using:
   - `scripts/run-dxf-diff.ps1`
   - `testdata/noop.lsp`
   - command `NOOP`

## Scope

- no authored linked `TABLECONTENT`
- no ATTDEF-backed block-cell values
- no block attributes
