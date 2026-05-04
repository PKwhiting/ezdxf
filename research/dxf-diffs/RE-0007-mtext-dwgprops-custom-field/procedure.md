# Procedure

1. Open `research/dxf-diffs/RE-0007-mtext-dwgprops-custom-field/before.dxf` in AutoCAD.
2. Open `DWGPROPS` and create a custom property:
   - Name: `ProjectCode`
   - Value: `VALUE-123`
3. Edit the only MTEXT entity.
4. Replace `FIELD_DWGPROPS_CUSTOM_BASE` with a field referencing the custom DWGPROPS property `ProjectCode`.
5. Save as AutoCAD 2018 ASCII DXF to `research/dxf-diffs/RE-0007-mtext-dwgprops-custom-field/after.dxf`.
6. Diff `before.dxf` and `after.dxf` to inspect the resulting field graph.

Files used in the final comparison:

- Baseline: `research/dxf-diffs/RE-0007-mtext-dwgprops-custom-field/before.dxf`
- Edited: `research/dxf-diffs/RE-0007-mtext-dwgprops-custom-field/after.dxf`
