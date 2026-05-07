# Findings

## Summary

Authored text-style overrides for `ACAD_TABLE` text cells are now validated.
AutoCAD preserves a local cell text-style override when it is written as:

- `91 = 262160`
- `7 = TABLE_ALT`

and the anonymous `*T` geometry block uses the same text style on the visible
MTEXT content.

## Confirmed Changes

1. All four probe variants were accepted by AutoCAD Core Console.
2. Only the `262160` probe preserved both the non-base override flag and the local `7 = TABLE_ALT` tag in the first cell record after roundtrip.
3. The `262152` probe did not preserve a local text-style tag. AutoCAD kept `64 = 0` instead, which does not match the intended text-style override surface.
4. The integrated validation sheet containing a real `set_cell_text_style()` case was also accepted by AutoCAD Core Console.
5. In the integrated sheet, the authored text-style override survived repeated saves unchanged:
   - `91 = 262160`
   - `7 = TABLE_ALT`

## Key Excerpts

Stable first-cell shell from the successful probe and integrated validation:

```text
91
   262160
7
TABLE_ALT
```

Successful `262160` probe before and after save:

```text
before.dxf
91
   262160
7
TABLE_ALT

after.dxf
91
   262160
7
TABLE_ALT
```

The integrated sheet also preserved the same authored pair:

```text
before.dxf
262160
TABLE_ALT

after.dxf
262160
TABLE_ALT
```

## Interpretation

- The validated text-style override bit is `16` relative to the base cell flag.
- The correct authored semantic-shell pattern is now evidence-based enough for a
  public helper.
- As with the other text-cell helpers, the semantic shell and rebuilt `*T`
  geometry block need to change together.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_acad_table_text_style_probe_variants.py`
- `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`

## Artifacts

- `experiments/acad-table-diffs/acad_table_text_style_probe_flag_262144.dxf`
- `experiments/acad-table-diffs/acad_table_text_style_probe_flag_262152.dxf`
- `experiments/acad-table-diffs/acad_table_text_style_probe_flag_262160.dxf`
- `experiments/acad-table-diffs/acad_table_text_style_probe_flag_262208.dxf`
- `experiments/acad-table-diffs/validate-acad-table-text-style-probe-262160/`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-text-style/`

## Non-Goals From This Experiment

- proving the exact meaning of every rejected probe bit pattern
- validating block-cell text-style behavior
- validating richer linked `TABLECONTENT` style semantics
