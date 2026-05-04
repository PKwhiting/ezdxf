# Procedure

1. Open `research/dxf-diffs/RE-0006-mtext-dwgprops-field/before.dxf` in AutoCAD.
2. Edit the only MTEXT entity.
3. Replace `FIELD_DWGPROPS_BASE` with a drawing-property field from the DWGPROPS family.
4. Recommended first property: `Title`.
5. Save as AutoCAD 2018 ASCII DXF to `research/dxf-diffs/RE-0006-mtext-dwgprops-field/after.dxf`.
6. Diff `before.dxf` and `after.dxf` to inspect the resulting field graph.

Files used in the final comparison:

- Baseline: `research/dxf-diffs/RE-0006-mtext-dwgprops-field/before.dxf`
- Edited: `research/dxf-diffs/RE-0006-mtext-dwgprops-field/after.dxf`
