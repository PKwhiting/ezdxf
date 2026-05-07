# Procedure

1. Generate the authored text-table validation sheet with:
   - `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`
2. Ensure that sheet includes two explicit authored cell overrides created by
   `ezdxf` before export:
   - title-cell text height override (`140 = 20.0`, `91 = 262176`)
   - header-cell alignment override (`170 = 4`, `91 = 262145`)
3. Save the generated DXF as:
   - `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
4. Open and re-save that DXF in AutoCAD Core Console using:
   - `scripts/run-dxf-diff.ps1`
   - `testdata/noop.lsp`
   - command `NOOP`
5. Diff the generated DXF against the first AutoCAD save to see what support
   structures AutoCAD synthesizes around the authored overrides.
6. Diff the first and second AutoCAD saves to verify whether the authored
   override tags remain stable across repeated saves.

## ezdxf Surface Under Test

- `layout.add_table(...)`
- `AcadTableBlockContent.set_cell_text_height(...)`
- `AcadTableBlockContent.set_cell_alignment(...)`
- `AcadTableBlockContent.rebuild_text_table_geometry()`

The override helpers update the semantic table cell and rebuild the anonymous
`*T` geometry block immediately so the visible graphics and exported table shell
stay in sync.
