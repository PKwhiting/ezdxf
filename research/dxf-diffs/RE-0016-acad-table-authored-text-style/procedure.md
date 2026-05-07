# Procedure

1. Generate a style-override probe matrix with:
   - `experiments/acad-table-diffs/generate_acad_table_text_style_probe_variants.py`
2. Create a custom text style in each generated DXF:
   - `TABLE_ALT`
   - font: `arial.ttf`
3. Author one text-cell style override candidate per file by writing:
   - local cell tag `7 = TABLE_ALT`
   - one candidate override flag value in the first cell record
4. Roundtrip each variant through AutoCAD Core Console using:
   - `scripts/run-dxf-diff.ps1`
   - `testdata/noop.lsp`
   - command `NOOP`
5. Compare the first saved cell record across variants to determine which flag
   pattern AutoCAD preserves together with `7 = TABLE_ALT`.
6. Once a stable pattern is identified, fold that helper into the integrated
   text-table validation sheet and run the broader AutoCAD/Core Console
   validation again.

## Variants Tested

- `262144`
- `262152`
- `262160`
- `262208`

## ezdxf Surface Under Test

- semantic shell export of local cell tag `7`
- rebuilt anonymous `*T` block MTEXT style
- `AcadTableBlockContent.set_cell_text_style(...)`
