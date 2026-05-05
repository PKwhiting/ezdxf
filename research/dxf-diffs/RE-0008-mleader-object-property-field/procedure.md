# Procedure

1. Generate a minimal baseline DXF containing:
   - one `LINE`
   - one plain `MULTILEADER` placeholder
   - Generator: `experiments/field-mleader-object/generate_baseline.py`
   - Baseline output: `experiments/field-mleader-object/generated/after.dxf`
2. Open the baseline in AutoCAD 2026.
3. Edit the `MULTILEADER` text content.
4. Replace the placeholder text with an object-property field referencing the line `Length` property.
5. Save as AutoCAD 2018 ASCII DXF.
6. Compare the generated baseline and edited file with `git diff --no-index`.
7. Run `scripts/run-dxf-diff.ps1` with `testdata/noop.lsp` to inspect the AutoCAD/Core Console re-save behavior.

Files used in the final comparison:

- Baseline: `experiments/field-mleader-object/generated/after.dxf`
- Edited: `experiments/field-mleader-object/manual/after-length-field.dxf`
- First Core Console save: `experiments/field-mleader-object/validate-manual-after-length-field/before.dxf`
- Second Core Console save: `experiments/field-mleader-object/validate-manual-after-length-field/after.dxf`
