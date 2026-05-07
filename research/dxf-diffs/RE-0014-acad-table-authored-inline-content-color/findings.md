# Findings

## Summary

Authored inline content color for `ACAD_TABLE` text cells survives repeated
AutoCAD saves unchanged. The validated storage model remains the same as the
 UI-authored baseline: color stays embedded in the cell text payload itself,
 not as a new local `AcDbTable` color tag or override-bit change.

## Confirmed Changes

1. The writer can now author inline text-cell color formatting by rewriting the cell payload string itself.
2. The helper preserves the existing minimal semantic-shell model: no new cell-local color tag is written and the override flag remains `91 = 262144`.
3. The anonymous `*T` geometry block is rebuilt after the payload rewrite, so the visible MTEXT content matches the exported cell payload immediately.
4. AutoCAD Core Console accepts the authored DXF and preserves the inline content-color payload across repeated saves.
5. The repeated-save diff again stays limited to helper-object/cache churn, not the authored semantic cell payload.

## Key Excerpts

Authored inline content-color payload:

```text
91
   262144
1
{\C215;\c10507177;A}
302
{\C215;\c10507177;A}
```

The same payload survives in both normalized snapshots:

```text
before.normalized.dxf
{\C215;\c10507177;A}

after.normalized.dxf
{\C215;\c10507177;A}
```

## Interpretation

- Inline content formatting is the correct next text-color write surface for the
  current `ACAD_TABLE` MVP.
- There is still no evidence that authored text-cell color should prefer a
  separate local `64` tag for the validated content-color case.
- Future text-formatting support should continue to prefer direct payload
  rewrites when that matches observed AutoCAD output.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`

## Artifacts

- `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-inline-color/`

## Non-Goals From This Experiment

- authored local `63/64/421` color-tag export for text cells
- block-cell color semantics
- full MTEXT inline-format editing beyond the color helper
