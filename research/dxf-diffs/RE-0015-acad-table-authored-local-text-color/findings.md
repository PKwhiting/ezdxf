# Findings

## Summary

Authored local text-color overrides for `ACAD_TABLE` text cells survive repeated
AutoCAD saves. The validated authored pattern matches the observed AutoCAD
baseline: `91 = 262150` with local `63`, `421`, and `283 = 0` tags.

## Confirmed Changes

1. The writer can now author the observed local text-color override pattern on text cells.
2. The exported override flag matches the AutoCAD baseline exactly: `262150`.
3. The exported local color tags also match the baseline shape:
   - `63 = 217`
   - `421 = 9643919`
   - `283 = 0`
4. AutoCAD Core Console accepts the authored DXF and preserves that local override pattern across repeated saves.
5. The repeated-save diff remains limited to helper-object/cache churn, not the authored semantic color tags.

## Key Excerpts

Authored local text-color override in the semantic shell:

```text
91
   262150
63
   217
421
  9643919
283
     0
```

The same values survive in both save snapshots:

```text
before.dxf
262150
217
9643919

after.dxf
262150
217
9643919
```

## Interpretation

- The local color-override pattern is now validated enough for an explicit
  authoring helper.
- This path is distinct from the inline payload-color helper:
  - inline color stays embedded in the text payload
  - local color uses semantic cell tags
- The exact semantic naming of these tags inside the `AcDbTable` shell is still
  less clear than the authored/export behavior, so the implementation should be
  treated as evidence-driven rather than reference-driven.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`

## Artifacts

- `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-local-color/`

## Non-Goals From This Experiment

- proving the exact Autodesk-internal meaning of each override bit
- block-cell color support
- full linked `TABLECONTENT` color authoring
