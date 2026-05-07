# Findings

## Summary

The `283` tag behaves like a fill/background enable-state indicator inside the
validated local fill override shell, but only in combination with a usable fill
color. The stable preserved "filled" state remains the UI-authored shape:

- `91 = 262150`
- `63 = <aci>`
- optional `421 = <true-color>`
- `283 = 0`

## Confirmed Changes

1. `63 = 45` with `283 = 0` survives as a local fill override.
2. `63 = 45` with no `283` is normalized by AutoCAD to the same preserved parsed state as the `283 = 0` variant.
3. `63 = 45` with `283 = 1` is normalized toward a disabled/no-fill state:
   - parsed as `fill_color = 0`
   - parsed as `fill_enabled = 1`
4. `283` without a usable fill color is also normalized to the same disabled/no-fill parsed state:
   - `fill_color = 0`
   - `fill_enabled = 1`
5. AutoCAD preserves the override flag `262150` across these variants, but the surviving color payload depends on the `63`/`283` combination.

## Key Excerpts

Preserved filled state:

```text
262150, 45, None, 0, 'T'
```

Normalized disabled/no-fill state:

```text
262150, 0, None, 1, 'T'
```

## Interpretation

- `283 = 0` is consistent with the validated enabled fill/background case.
- `283 = 1` is consistent with a disabled/no-fill state.
- A future explicit disable helper could be justified, but the current validated
  public authoring surface only needs the enabled fill helper.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_acad_table_fill_enable_probe_variants.py`

## Artifacts

- `experiments/acad-table-diffs/acad_table_fill_enable_probe_aci_283_0.dxf`
- `experiments/acad-table-diffs/acad_table_fill_enable_probe_aci_283_1.dxf`
- `experiments/acad-table-diffs/acad_table_fill_enable_probe_aci_no_283.dxf`
- `experiments/acad-table-diffs/acad_table_fill_enable_probe_no_color_283_0.dxf`
- `experiments/acad-table-diffs/acad_table_fill_enable_probe_no_color_283_1.dxf`

## Non-Goals From This Experiment

- defining a public fill-disable API yet
- proving the exact UI wording used by AutoCAD for the enabled/disabled state
