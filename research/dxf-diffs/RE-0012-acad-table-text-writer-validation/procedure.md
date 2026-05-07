# Procedure

1. Generate a text-only `ACAD_TABLE` validation drawing authored entirely by
   `ezdxf` with:
   - `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`
2. Save the generated DXF as:
   - `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
3. Open and re-save that DXF in AutoCAD Core Console by running:
   - `scripts/run-dxf-diff.ps1`
   - input: `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
   - lisp: `testdata/noop.lsp`
   - command: `NOOP`
4. Diff the generated DXF against the first AutoCAD save (`before.dxf`) to see
   which support objects AutoCAD synthesizes from the minimal authored shell.
5. Diff `before.dxf` against `after.dxf` to separate one-time canonicalization
   from repeated-save instability.

## Validation Sheet Content

- one 3-row x 2-column role-row table (`title`, `header`, `data`)
- one 2-row x 2-column table with title suppressed and explicit row heights
- one 1-row x 3-column table with title and header suppressed

All tables are authored through `layout.add_table(...)` and exported without
prebuilt `TABLECONTENT`, `TABLEGEOMETRY`, or `ACAD_XREC_ROUNDTRIP` objects.
