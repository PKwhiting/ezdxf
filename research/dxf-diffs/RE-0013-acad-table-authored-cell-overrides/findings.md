# Findings

## Summary

Authored text-cell overrides for `ACAD_TABLE` now survive real AutoCAD
roundtrips. A text-height override written as local `140` plus override flag
`91 = 262176`, and an alignment override written as local `170` plus override
flag `91 = 262145`, are both preserved across repeated AutoCAD saves.

## Confirmed Changes

1. The text-only writer can now author local text-height overrides on text cells.
2. The text-only writer can now author local alignment overrides on text cells.
3. The anonymous `*T` geometry block is rebuilt when these overrides are applied, so the visible MTEXT geometry matches the authored semantic shell before export.
4. AutoCAD Core Console accepts the authored override DXF without requiring prebuilt `TABLECONTENT`, `TABLEGEOMETRY`, or `ACAD_XREC_ROUNDTRIP` objects in the source file.
5. AutoCAD still synthesizes those helper objects on the first save, but the authored `AcDbTable` override tags remain stable across repeated saves.

## Key Excerpts

Authored title-cell text-height override that survived repeated saves:

```text
91
   262176
140
20.0
```

Authored header-cell alignment override that survived repeated saves:

```text
91
   262145
170
     4
```

Repeated-save comparison kept both override records unchanged in the semantic
table shell:

```text
141
29.66666666666667
...
91
   262176
140
20.0
```

```text
280
     1
...
91
   262145
170
     4
```

The remaining repeated-save diff stayed in generated roundtrip-support handles:

```text
361
-C0
+D6
...
361
-C4
+DA
```

## Interpretation

- The next useful writer tier after the minimal shell is viable without full
  linked `TABLECONTENT` authoring.
- Text-height and alignment are good first write-side overrides because they map
  to stable local `AcDbTable` tags and to directly rebuildable MTEXT geometry.
- The rebuild step is necessary: authored semantic overrides alone are not
  enough if the anonymous `*T` block is left stale.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`

## Artifacts

- `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation-overrides/`

## Non-Goals From This Experiment

- authored `TABLECONTENT` export
- authored block-cell overrides
- byte-level reproduction of AutoCAD-generated helper objects
