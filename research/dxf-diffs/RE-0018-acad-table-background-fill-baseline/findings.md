# Findings

## Summary

The UI-authored title-cell background/fill baselines confirm that the local tag
pattern previously treated as a text-color override is actually a fill/background
override surface.

## Confirmed Changes

1. The UI-authored ACI fill override uses the semantic shell pattern:
   - `91 = 262150`
   - `63 = 45`
   - `283 = 0`
2. The UI-authored true-color fill override uses the semantic shell pattern:
   - `91 = 262150`
   - `63 = 177`
   - `421 = 3811732`
   - `283 = 0`
3. In both UI-authored files, the visible `*T` block MTEXT remains uncolored:
   - `color = 0`
   - no `true_color`
4. This distinguishes the semantic shell fill/background override from the
   separate inline payload-color path, which colors the text content string
   itself.

## Key Excerpts

ACI fill baseline:

```text
91
   262150
63
    45
283
     0
```

True-color fill baseline:

```text
91
   262150
63
   177
421
3811732
283
     0
```

Parsed `virtual_entities()` from both baselines keep the first MTEXT uncolored:

```text
[(0, None, 'TITLE'), (0, None, 'HEADER'), (0, None, 'DATA')]
```

## Interpretation

- The validated semantic meaning of the current helper surface is fill/background
  override, not text-color override.
- The canonical public helper name should therefore be `set_cell_fill_color()`.
- The existing `set_cell_text_color()` name can remain as a compatibility alias,
  but it should no longer be documented as the primary meaning of the API.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_acad_table_fill_override_seed.py`

## Artifacts

- `experiments/acad-table-diffs/acad_table_012_true_title_fill_aci_override.dxf`
- `experiments/acad-table-diffs/acad_table_013_true_title_fill_true_color_override.dxf`

## Non-Goals From This Experiment

- proving how AutoCAD renders the fill visually in every display mode
- block-cell fill semantics
- full linked `TABLECONTENT` fill semantics
