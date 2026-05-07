# Procedure

## Goal

Establish a clean UI-authored `ACAD_TABLE` baseline for text-cell background/fill
 overrides, so the current ambiguous `63` / `421` / `283` cell-local pattern can
 be tied to a specific visible AutoCAD action instead of inferred only from raw
 DXF tags.

## Seed Artifact

- Seed generator:
  - `experiments/acad-table-diffs/generate_acad_table_fill_override_seed.py`
- Seed DXF:
  - `experiments/acad-table-diffs/acad_table_fill_override_seed.dxf`

Regenerate the seed at any time by running the generator script.

## Manual AutoCAD Workflow

1. Open `acad_table_fill_override_seed.dxf` in AutoCAD.
2. Select the title cell only.
3. Apply exactly one controlled change:
   - Variant A: enable background fill with an ACI color only.
   - Variant B: enable background fill with a true-color value.
4. Do not change text, text height, alignment, style, table style, row heights,
   column widths, or the visible cell text payload.
5. Save each edited drawing as a new file in `experiments/acad-table-diffs/`.

Suggested filenames:

- `acad_table_012_true_title_fill_aci_override.dxf`
- `acad_table_013_true_title_fill_true_color_override.dxf`

6. Save each edited file a second time and diff first-save vs second-save output
   to separate authoring structure from AutoCAD canonicalization noise.

## Questions

- Which cell-local tags represent UI-authored background/fill overrides?
- Does the UI-authored action affect the semantic shell only, the generated
  `TABLECONTENT` wrappers, or both?
- Which override bits in cell-local `91` correspond to the fill/background case?
- Does AutoCAD color the visible `*T` block MTEXT geometry, create a fill-only
  semantic override, or both?
