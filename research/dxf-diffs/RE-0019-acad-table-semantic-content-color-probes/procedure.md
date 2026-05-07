# Procedure

## Goal

Probe whether there is a stable semantic-shell text-content color path for
`ACAD_TABLE` text cells beyond:

- inline payload color formatting (`{\C...;\c...;...}`)
- local fill/background overrides (`91 = 262150` with `63` / `421` / `283`)

## Probe Matrix

Generate four minimal DXF variants with:

- `experiments/acad-table-diffs/generate_acad_table_content_color_probe_variants.py`

Variant tags inserted into the first cell only:

1. `64 = 217`, `91 = 262146`
2. `64 = 217`, `91 = 262150`
3. `64 = 217`, `420 = 9643919`, `91 = 262146`
4. `64 = 217`, `420 = 9643919`, `91 = 262150`

## Validation

1. Roundtrip each probe through AutoCAD Core Console using:
   - `scripts/run-dxf-diff.ps1`
   - `testdata/noop.lsp`
   - command `NOOP`
2. Load each first-save snapshot through `ezdxf` and inspect the first parsed
   `AcadTableCell`.
3. Compare whether local `64` / `420` tags survive, are rewritten, or are
   discarded.
