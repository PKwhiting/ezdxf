# Procedure

1. Generate the authored text-table validation sheet with:
   - `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`
2. Ensure one text cell is authored with inline content-color formatting through:
   - `AcadTableBlockContent.set_cell_content_color(...)`
3. Save the generated DXF as:
   - `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
4. Open and re-save that DXF in AutoCAD Core Console using:
   - `scripts/run-dxf-diff.ps1`
   - `testdata/noop.lsp`
   - command `NOOP`
5. Diff the first and second AutoCAD saves to verify whether the inline color
   payload survives repeated saves without being rewritten into separate local
   color tags.

## ezdxf Surface Under Test

- `AcadTableCell.set_content_color(...)`
- `AcadTableBlockContent.set_cell_content_color(...)`

The helper rewrites the text payload itself using MTEXT inline color commands,
then rebuilds the anonymous `*T` geometry block so the visible MTEXT content
matches the semantic table shell.
