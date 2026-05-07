# Procedure

1. Generate the authored text-table validation sheet with:
   - `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`
2. Ensure one text cell is authored with the local color override helper:
   - `AcadTableBlockContent.set_cell_text_color(...)`
3. Save the generated DXF as:
   - `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
4. Open and re-save that DXF in AutoCAD Core Console using:
   - `scripts/run-dxf-diff.ps1`
   - `testdata/noop.lsp`
   - command `NOOP`
5. Compare the generated DXF with the first AutoCAD save to confirm acceptance.
6. Compare the first and second AutoCAD saves to verify whether the authored
   local color tags remain stable.

## ezdxf Surface Under Test

- `AcadTableCell.set_text_color(...)`
- `AcadTableBlockContent.set_cell_text_color(...)`

The helper writes the validated local tag pattern seen in the AutoCAD baseline:

- `91 = 262150`
- `63 = <aci>`
- `421 = <true-color>`
- `283 = 0`

and rebuilds the anonymous `*T` geometry block so the visible MTEXT content is
colored consistently with the semantic table shell.
