# Notes

## Why This Experiment Matters

`HATCH.Area` already worked for simple loops, simple holes, and several single
edge-path cases. The unresolved gap was a hatch with a bulged inner hole loop.
The key question was whether AutoCAD treated that geometry as a normal nested
hole or rewrote it into a different internal boundary representation.

## Important Observation

AutoCAD does not preserve the original two-loop source geometry inside the
stored HATCH. Instead, the saved HATCH contains a single polyline boundary path
with six vertices and two small bulge values that directly outline the filled
region.

That means there are two different authoring situations:

1. raw multi-path bulged-hole hatches created directly by `ezdxf`
2. canonicalized single-path hatches saved by AutoCAD after interactive hatch creation

The current `ezdxf` area logic matches the second case but not the first one.
