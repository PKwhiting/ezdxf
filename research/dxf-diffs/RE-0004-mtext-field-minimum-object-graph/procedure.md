# Procedure

1. Use the UI-authored `AcVar Author` field DXF from `RE-0001` as the source drawing.
2. Generate three reduction variants from the source DXF by removing one part of the field graph at a time:
   - remove only the root `ACAD_FIELDLIST` dictionary entry
   - remove the `FIELDLIST` object and the root `ACAD_FIELDLIST` entry
   - remove the host `MTEXT` `ACAD_XDICTIONARY` block
3. Open each variant in AutoCAD Core Console and save immediately using a no-op AutoLISP command.
4. Inspect the saved `before.dxf` snapshots to determine which missing structures AutoCAD rebuilt and which it did not.

Files used in the final comparison:

- Source field DXF: `experiments/field-mtext/generated/after.dxf`
- Variant directory: `experiments/field-mtext-reduction/variants/`
- Roundtrip directory: `experiments/field-mtext-reduction/roundtrip-*`
