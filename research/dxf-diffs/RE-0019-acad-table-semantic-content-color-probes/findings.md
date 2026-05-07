# Findings

## Summary

No stable semantic-shell text-content color path was validated by the probe
matrix. AutoCAD accepts the candidate `64` / `420` cell-local tag combinations,
but strips them back to the plain base text cell on the first save.

## Confirmed Changes

1. All four probe variants open successfully in AutoCAD Core Console.
2. After the first AutoCAD save, the first text cell in every variant is reduced back to the plain base shell:
   - `91 = 262144`
   - no surviving local `64`
   - no surviving local `420`
3. The parsed first cell after roundtrip is the plain text cell in all cases:
   - `override_flags = 262144`
   - `content_color = None`
   - `fill_color = None`
   - `fill_true_color = None`
   - `fill_enabled = None`

## Key Excerpts

Parsed first cell after AutoCAD save for all four probe variants:

```text
262144, None, None, None, None, 'T'
```

This means the candidate semantic-shell `64` / `420` tags were not preserved as
authoritative table data.

## Interpretation

- The validated text-color surfaces remain:
  - inline payload formatting in the cell text string
  - and no separate semantic-shell text-content color path is currently proven
- The validated semantic-shell color surface remains the fill/background path,
  not a content-color path.
- The `AcadTableCell.content_color` read model may still be useful for raw DXFs,
  but there is no evidence yet to support a public authoring helper for it.

## Likely ezdxf Targets

- `experiments/acad-table-diffs/generate_acad_table_content_color_probe_variants.py`
- `src/ezdxf/entities/acad_table.py`

## Artifacts

- `experiments/acad-table-diffs/acad_table_content_color_probe_64_flag_262146.dxf`
- `experiments/acad-table-diffs/acad_table_content_color_probe_64_flag_262150.dxf`
- `experiments/acad-table-diffs/acad_table_content_color_probe_64_420_flag_262146.dxf`
- `experiments/acad-table-diffs/acad_table_content_color_probe_64_420_flag_262150.dxf`

## Non-Goals From This Experiment

- proving there is no possible semantic content-color path at all
- testing arbitrary additional undocumented bit patterns beyond the focused probe
  matrix
