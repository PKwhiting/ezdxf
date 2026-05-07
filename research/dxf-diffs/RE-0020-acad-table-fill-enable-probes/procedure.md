# Procedure

## Goal

Clarify the authored meaning of cell-local tag `283` for the validated
background/fill override shell.

## Probe Matrix

Generate the variants by:

- `experiments/acad-table-diffs/generate_acad_table_fill_enable_probe_variants.py`

First-cell combinations tested:

1. `91 = 262150`, `63 = 45`, `283 = 0`
2. `91 = 262150`, `63 = 45`, `283 = 1`
3. `91 = 262150`, `63 = 45`, no `283`
4. `91 = 262150`, no `63`, `283 = 0`
5. `91 = 262150`, no `63`, `283 = 1`

## Validation

1. Roundtrip each probe through AutoCAD Core Console.
2. Load the first-save snapshots through `ezdxf`.
3. Inspect the first parsed `AcadTableCell` values for:
   - `override_flags`
   - `fill_color`
   - `fill_true_color`
   - `fill_enabled`
