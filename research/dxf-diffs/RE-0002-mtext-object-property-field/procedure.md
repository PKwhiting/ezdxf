# Procedure

1. Generate a minimal baseline DXF containing:
   - one geometry object with a stable measurable property
   - one plain `MTEXT` placeholder
   - Generator LISP: `testdata/make-field-mtext-object-base.lsp`
   - Current generated baseline: `experiments/field-mtext-object/generated/after.dxf`
2. Open the baseline in AutoCAD 2026.
3. Edit the `MTEXT` entity.
4. Replace the placeholder text with an object-property field referencing the line `Length` property.
5. Save as AutoCAD 2018 ASCII DXF.
6. Diff the baseline and edited DXF with `scripts/diff-dxf.ps1`.

Files used in the final comparison:

- Baseline: `experiments/field-mtext-object/generated/after.dxf`
- Edited: `experiments/field-mtext-object/manual/after-length-field.dxf`
