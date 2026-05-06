# Procedure

1. Build a source DXF containing:
   - object-backed fields on `MTEXT`, `TEXT`, and attached `ATTRIB`
   - custom `MLEADERSTYLE` entries
   - MTEXT-content `MULTILEADER`
   - block-content `MULTILEADER`
   - explicit `MultiLeader.arrow_heads`
2. Generate Python reconstruction code with:
   - `block_to_code(...)` for required block definitions
   - `table_entries_to_code(...)` for required `MLEADERSTYLE` objects
   - `entities_to_code(...)` for modelspace entities
3. Execute the generated Python source into a fresh DXF document.
4. Save the rebuilt document as `dxf2code_roundtrip_validation.dxf`.
5. Open and resave that file in AutoCAD Core Console with the existing no-op validation harness.
6. Diff the produced `before.dxf` and `after.dxf` snapshots to classify remaining changes.
