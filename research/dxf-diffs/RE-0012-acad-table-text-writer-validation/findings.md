# Findings

## Summary

The first text-only `ACAD_TABLE` writer is structurally acceptable to AutoCAD.
AutoCAD opens and re-saves a DXF authored from the minimal semantic shell plus
anonymous `*T` geometry block, then synthesizes the richer linked table support
objects on the first save.

## Confirmed Changes

1. A validation sheet containing three different text-only table layouts created only by `layout.add_table(...)` is accepted by AutoCAD Core Console.
2. The authored DXF does not need prebuilt `TABLECONTENT`, `TABLEGEOMETRY`, or `ACAD_XREC_ROUNDTRIP` support objects to open successfully.
3. On the first AutoCAD save, AutoCAD synthesizes linked table support structures from the minimal authored shell, including:
   - `TABLECONTENT`
   - `TABLEGEOMETRY`
   - `ACAD_XREC_ROUNDTRIP`
   - `ACAD_ROUNDTRIP_2008_TABLE_ENTITY`
   - `CELLSTYLEMAP`
   - `ACDSDATA` cache/schema records
4. The authored `AcDbTable` semantic shell remains stable across the repeated AutoCAD save. The repeated-save diff did not show row/column counts, row heights, column widths, suppression flags, or cell text payloads changing.
5. The remaining `before.dxf` -> `after.dxf` deltas are limited to roundtrip-support handle churn and binary/cache rewrites inside generated table support data.

## Key Excerpts

Repeated-save stability for the semantic shell of the first table:

```text
100
AcDbTable
280
     0
342
22
343
33
...
91
        3
92
        2
141
11.0
141
9.0
141
9.0
142
38.0
142
28.0
```

Generated DXF to first AutoCAD save: new linked support objects appear, for
example:

```text
0
TABLECONTENT
...
100
AcDbTableGeometry
...
3
ACAD_XREC_ROUNDTRIP
...
102
ACAD_ROUNDTRIP_2008_TABLE_ENTITY
```

Repeated-save diff stays in generated roundtrip support handles rather than the
table shell itself:

```text
361
-A9
+BF
...
361
-AD
+C3
...
361
-B1
+C7
```

## Interpretation

- The current minimal writer shape is viable: semantic `AcDbTable` shell,
  anonymous `*T` geometry block, and `TABLESTYLE` binding are enough for a
  first authored export.
- Explicit write support for `TABLECONTENT`, `TABLEGEOMETRY`, and roundtrip
  helper objects can remain deferred while the text-only writer surface is
  expanded.
- Future work should focus on intentional authored semantics such as cell-local
  overrides or linked block-cell content, not on reproducing AutoCAD's cache and
  support-object churn byte-for-byte.

## Likely ezdxf Targets

- `src/ezdxf/entities/acad_table.py`
- `src/ezdxf/graphicsfactory.py`
- `tests/test_01_dxf_entities/test_138_acad_table.py`
- `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`

## Artifacts

- `experiments/acad-table-diffs/ezdxf_text_table_validation.dxf`
- `experiments/acad-table-diffs/generate_ezdxf_text_table_validation.py`
- `experiments/acad-table-diffs/validate-ezdxf-text-table-validation/`

## Non-Goals From This Experiment

- proving byte-level parity with AutoCAD-authored table support objects
- validating block-cell authoring
- validating explicit authored `TABLECONTENT` export
