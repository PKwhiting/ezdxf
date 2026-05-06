# Findings

## Summary

AutoCAD saves the UI-authored bulged-hole hatch as a single canonicalized
polyline boundary path, and `ezdxf`'s current `HATCH.Area` inference matches
that canonicalized representation. The remaining unsupported case is specifically
the raw multi-path bulged-hole hatch representation authored directly by
`ezdxf`.

## Confirmed Changes

1. The manual AutoCAD hatch no longer stores the original outer loop plus inner bulged hole loop as two paths.
2. Instead, AutoCAD stores one polyline boundary path with six vertices and two small bulges.
3. A probe field attached to that saved HATCH resolves to `47.0397` in AutoCAD.
4. The current `ezdxf` `HATCH.Area` inference computes the same value for that canonicalized single-path boundary.
5. Raw multi-path bulged-hole hatches still produce different AutoCAD area values that do not follow the simple hole-subtraction rules already implemented for non-bulged holes.

## Key Excerpts

The canonicalized HATCH in the manually authored file uses a single polyline boundary path:

```text
91
        1
92
        7
72
        1
73
        1
93
        6
10
8.0
20
8.0
...
10
2.0
20
2.0
42
0.1844830881382522
...
10
7.236067977499788
20
0.0
42
0.1844830881382522
```

The attached probe field resolves to:

```text
1
47.0397
```

## Interpretation

- `HATCH.Area` for AutoCAD-authored bulged-hole hatches is already effectively supported once the HATCH has been canonicalized by AutoCAD.
- The unresolved problem is narrower than before: it is about reproducing AutoCAD's canonicalization or equivalent area semantics for raw multi-path bulged-hole input.
- That canonicalization is not a simple orientation or bulge-sign rule; the stored boundary itself changes shape.

## Likely ezdxf Targets

- `src/ezdxf/entities/mtext.py`
- `src/ezdxf/entities/boundary_paths.py`

## Non-Goals From This Experiment

- implementing the raw multi-path bulged-hole canonicalization
- proving support for MPOLYGON area
