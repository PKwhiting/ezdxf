# Findings

## Summary

AutoCAD does not canonicalize the anonymous `*T` block MTEXT colors for the
validated local semantic color override case. Two DXFs with the same semantic
cell-local color tags but different `*T` MTEXT colors are both accepted and both
remain unchanged across repeated saves.

## Confirmed Changes

1. The semantic local color shell is stable in both variants:
   - `91 = 262150`
   - `63 = 217`
   - `421 = 9643919`
   - `283 = 0`
2. AutoCAD accepts a variant whose first cell MTEXT in the `*T` block is explicitly colored to match the semantic shell.
3. AutoCAD also accepts a variant whose first cell MTEXT in the `*T` block remains uncolored (`color = 0`, no `true_color`).
4. AutoCAD preserves the geometry difference across repeated saves instead of rewriting both variants to a single canonical form.

## Key Excerpts

Colored-geometry variant after AutoCAD save, inspected through `virtual_entities()`:

```text
[(217, 9643919, 'T'), (0, None, 'H'), (0, None, 'D')]
```

Uncolored-geometry variant after AutoCAD save, inspected through `virtual_entities()`:

```text
[(0, None, 'T'), (0, None, 'H'), (0, None, 'D')]
```

The semantic cell state stayed identical in both cases:

```text
262150, 217, 9643919, 0
```

## Interpretation

- The semantic local color override is validated.
- The `*T` block color mirroring rule is still not uniquely determined by
  AutoCAD behavior.
- The current `ezdxf` helper may keep coloring rebuilt MTEXT for better
  `virtual_entities()` fidelity, but that choice is convenience-driven rather
  than forced by AutoCAD canonicalization.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `experiments/acad-table-diffs/generate_acad_table_local_color_geometry_variants.py`

## Artifacts

- `experiments/acad-table-diffs/acad_table_local_color_variant_geometry_colored.dxf`
- `experiments/acad-table-diffs/acad_table_local_color_variant_geometry_uncolored.dxf`
- `experiments/acad-table-diffs/validate-acad-table-local-color-geometry_colored/`
- `experiments/acad-table-diffs/validate-acad-table-local-color-geometry_uncolored/`

## Non-Goals From This Experiment

- choosing the final public helper behavior for `virtual_entities()` rendering
- proving which variant matches AutoCAD's on-screen renderer more closely
