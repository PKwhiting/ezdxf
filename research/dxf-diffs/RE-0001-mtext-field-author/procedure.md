# Procedure

1. Generate a minimal baseline DXF containing a single `MTEXT` entity with text `FIELD_BASE`.
   - Generator LISP: `testdata/make-field-mtext-base.lsp`
   - Runner: `scripts/run-dxf-diff.ps1`
2. Open the generated DXF in AutoCAD 2026.
3. Edit the lone `MTEXT` entity.
4. Replace the plain text with a field for the Author drawing variable.
5. Save as AutoCAD 2018 ASCII DXF.
6. Because the edited file overwrote the generated baseline, regenerate the plain baseline using the same generator LISP.
7. Diff regenerated plain baseline against the edited DXF using `scripts/diff-dxf.ps1`.

Files used in the final comparison:

- Baseline: `experiments/field-mtext/regen-plain/after.dxf`
- Edited: `experiments/field-mtext/generated/after.dxf`
