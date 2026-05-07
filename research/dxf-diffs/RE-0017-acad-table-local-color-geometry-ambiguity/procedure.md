# Procedure

1. Generate two `ACAD_TABLE` variants with the same semantic local color
   override:
   - `experiments/acad-table-diffs/generate_acad_table_local_color_geometry_variants.py`
2. Keep the semantic shell identical in both variants:
   - `91 = 262150`
   - `63 = 217`
   - `421 = 9643919`
   - `283 = 0`
3. Change only the anonymous `*T` block MTEXT color state:
   - variant A: first cell MTEXT colored to match the semantic override
   - variant B: first cell MTEXT left uncolored (`color = 0`, no `true_color`)
4. Roundtrip both variants through AutoCAD Core Console using:
   - `scripts/run-dxf-diff.ps1`
   - `testdata/noop.lsp`
   - command `NOOP`
5. Load the resulting `before.dxf` and `after.dxf` snapshots through `ezdxf`
   and inspect:
   - semantic cell override tags
   - `virtual_entities()` MTEXT color values

## Goal

Determine whether AutoCAD canonicalizes the `*T` block MTEXT colors for local
semantic color overrides, or preserves both colored and uncolored geometry.
