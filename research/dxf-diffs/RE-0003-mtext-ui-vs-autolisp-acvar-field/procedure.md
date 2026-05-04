# Procedure

1. Create a baseline DXF containing a single plain `MTEXT` placeholder.
   - Current UI baseline: `experiments/field-mtext-acvar-compare/generated-ui-baseline/after.dxf`
2. Create one AutoCAD UI-authored `AcVar` field in `MTEXT`.
   - Replace `FIELD_BASE` with an `Author` drawing variable field.
   - Save as `experiments/field-mtext-acvar-compare/manual/after-ui-author-field.dxf`.
3. Create one AutoLISP-authored inline `AcVar` field in an equivalent baseline.
   - Current AutoLISP output: `experiments/field-mtext-acvar-compare/generated-autolisp/after.dxf`
4. Save both results as AutoCAD 2018 ASCII DXF.
5. Diff the two outputs and compare the resulting `MTEXT`, extension dictionary, `FIELDLIST`, and `FIELD` structures.

Files used in the final comparison:

- UI baseline: `experiments/field-mtext-acvar-compare/generated-ui-baseline/after.dxf`
- UI-authored result: `experiments/field-mtext-acvar-compare/manual/after-ui-author-field.dxf`
- AutoLISP-authored result: `experiments/field-mtext-acvar-compare/generated-autolisp/after.dxf`
