# Findings

## Summary

The first authored linked `TABLECONTENT` path for attributed block cells is now
structurally acceptable to AutoCAD, but the ATTDEF-backed value payload still
does not survive the first AutoCAD save as semantic linked cell content.

## Confirmed Changes

1. The authored DXF containing a block cell plus linked `TABLECONTENT` with ATTDEF-backed `330` / `301` value pairs is accepted by AutoCAD Core Console.
2. The `TABLECONTENT` object and `ACAD_XREC_ROUNDTRIP` link both survive the first save.
3. The block cell itself also survives as a real block cell in the semantic `AcDbTable` shell.
4. The authored attribute payload (`X` / `Y`) is stripped by AutoCAD from the linked attributed cell payload on the first save.
5. The same `X` / `Y` values still survive in the wrapper block as real attached `ATTRIB` entities.
6. `ezdxf` now recovers those surviving values through a wrapper-geometry fallback in `get_cell_block_attribs()`.
7. Matching the UI baseline's first display-text `FORMATTEDCELLCONTENT` shape was not sufficient to preserve the two-content linked payload on AutoCAD save.
8. Removing the extra single-line R2018 `ATTRIB` export tags (`71` / `72`) and restoring the obvious wrapper `MTEXT` defaults was also not sufficient.
9. A first-save Core Console roundtrip of the UI-authored baseline `acad_table_014_true_block_cell_with_attribs_ui_minimal.dxf` preserves the two-content linked payload, its wrapper metadata, and the linked `330` / `301` attribute tuples.
10. Matching the visible wrapper `ATTRIB` `280/2/70/280` pattern and wrapper `MTEXT` `73` tag still did not prevent AutoCAD from collapsing the authored linked attributed cell on first save.
11. The previous authored `361` companion defect was real: `ezdxf` was exporting a generic placeholder instead of a typed `TABLEGEOMETRY` object.
12. After adding a real typed `TABLEGEOMETRY` export, AutoCAD still collapses the authored linked attributed cell on first save.
13. Matching the UI baseline's `ACAD_XREC_ROUNDTRIP` reactor link back to the owning extension dictionary was also not sufficient.
14. A separate probe table authored with the same visible `T / H / D` content profile as the UI baselines still collapses on first save, so the remaining gap is not caused by the longer `TITLE / HEADER` text used in the broader validation sheet.
15. `ezdxf` had a separate malformed-DXF bug where authored `ACAD_TABLE` entities exported `330 None` because the table class did not support layout owner assignment through `set_owner()`.
16. Fixing the `ACAD_TABLE` owner so authored files export a valid layout owner handle also does not prevent AutoCAD from collapsing the linked attributed cell on first save.
17. Direct DXF surgery showed that the authored `TABLECONTENT`, authored wrapper block, and authored `*T` geometry block each survive when grafted individually into the UI baseline with valid handle remapping.
18. Replacing only the `ACAD_TABLE` shell in the surviving UI baseline with the authored shell is sufficient to trigger the first-save collapse.
19. Updating the authored shell export to match the UI shell more closely for attributed block cells (`340 = wrapper block record`, `179 = 0`, and UI-like ordering) was still not sufficient to preserve the linked attributed payload in the fully authored file.

## Interpretation

- File validity and object-graph acceptance are no longer the problem.
- The remaining blocker is the exact linked-cell content shape required for ATTDEF-backed values to be preserved semantically in linked `TABLECONTENT`.
- Effective read support is now stronger than write support for this case, because AutoCAD-saved files can still be resolved from surviving wrapper `ATTRIB` entities.
- The remaining gap is still real after correcting the most obvious linked-content and wrapper-shape mismatches, because the UI-authored baseline survives the same first-save cycle without collapsing.
- The remaining gap is still real after correcting the visible linked payload, wrapper block tags, and the typed `TABLEGEOMETRY` companion.
- The next likely deltas are now hidden or less obvious support-object semantics: `ACAD_XREC_ROUNDTRIP` linkage details, fuller `TABLEGEOMETRY` payload semantics, or additional object/reactor metadata not yet authored.
- The remaining gap is not explained by visible cell content text differences between the UI baselines and the authored validation sheet.
- The remaining gap is not explained by the previously malformed table owner either, although that export bug was real and is now fixed.
- The strongest remaining evidence points to the semantic `AcDbTable` shell itself as the trigger surface, not the linked support objects in isolation.
- Even after the shell export was brought closer to the UI baseline for attributed block cells, AutoCAD still normalized the linked payload away, so at least one additional shell-side semantic difference remains.
- The next iteration should compare the authored linked block-cell section against `acad_table_014_true_block_cell_with_attribs_ui_minimal.dxf` field-by-field until the first-save linked payload survives.

## Artifacts

- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-block-cell-attribs-v15/`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-block-cell-attribs-v17/`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-block-cell-attribs-v19/`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-block-cell-attribs-v20/`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-block-cell-attribs-v21/`
- `experiments/acad-table-diffs/acad_table_014_true_block_cell_with_attribs_ui_minimal.dxf`
- `experiments/acad-table-diffs/validate-acad-table-014-ui-attrib-baseline-v1/`
- `experiments/acad-table-diffs/ezdxf_text_table_validation_ui_content_probe.dxf`
- `experiments/acad-table-diffs/validate-ezdxf-ui-content-probe-v1/`
- `experiments/acad-table-diffs/validate-ezdxf-ui-content-probe-v2/`
- `experiments/acad-table-diffs/validate-acad-table-014-ui-replace-table-shell-v1/`
- `experiments/acad-table-diffs/validate-ezdxf-ui-content-probe-v7/`
