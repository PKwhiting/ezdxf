# Findings

## Summary

The first minimal authored block-cell export is accepted by AutoCAD. A block
cell written directly in the semantic `AcDbTable` shell, with no authored linked
`TABLECONTENT`, survives the first AutoCAD/Core Console save when the anonymous
`*T` geometry block contains a visible `INSERT` of the target block.

## Confirmed Changes

1. The authored block-cell shell survives the first AutoCAD save with the expected minimal semantic tags:
   - `171 = 2`
   - `91 = 262145`
   - `340 = <block-record-handle>`
   - `144 = 1.0`
   - `179 = 0`
   - `170 = 1`
2. The loaded table after AutoCAD save is still parsed as a block cell by `ezdxf`.
3. The visible authored geometry also survives in the `*T` block as a simple `INSERT` of the target block.
4. This validates a first authored block-cell path without authored linked `TABLECONTENT`, as long as no ATTDEF-backed values are required.

## Key Excerpts

Parsed saved cell state:

```text
cell 2 262145 <block-record-handle> 1.0 0 1 ''
```

The saved virtual geometry still contains the block reference:

```text
('INSERT', {'name': 'TABLE_BLOCK_CELL_MIN', ...})
```

## Interpretation

- A minimal block-cell helper is justified as an experimental public surface.
- Authored linked `TABLECONTENT` is not a prerequisite for the first no-attribute
  block-cell export.
- ATTDEF-backed block-cell values should remain a later increment, because that
  still needs authored linked `TABLECONTENT` support.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`

## Artifacts

- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-block-cell/`

## Non-Goals From This Experiment

- authored block-cell attributes
- authored linked `TABLECONTENT`
- byte-level parity with AutoCAD-authored block-cell geometry wrappers
