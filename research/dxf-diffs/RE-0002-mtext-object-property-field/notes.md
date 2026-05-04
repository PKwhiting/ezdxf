# Notes

## Recommended Geometry Choice

Use the smallest possible object-property example.

Current baseline already uses the preferred first option:

- one `LINE`
- one plain `MTEXT` placeholder

Recommended first option:

1. one `LINE`
2. field referencing line length

Alternative:

1. one closed `LWPOLYLINE`
2. field referencing area

The line-length case is preferred first because it minimizes unrelated entity complexity.

## Why This Experiment Matters

`RE-0001` established that UI-authored `MTEXT` fields are object-backed. This next experiment should reveal how AutoCAD stores a reference to another entity, which is likely the core requirement for useful `ezdxf` field authoring support.

Result: this experiment confirmed that object references are not only implicit in field code text. AutoCAD also stores explicit DXF object references inside the child `FIELD` object.

## Next Setup Task

Natural follow-ups:

1. Compare this UI-authored object-property field with an AutoLISP-authored inline object-property field.
2. Identify the minimum subset of `FIELD`/`FIELDLIST`/dictionary structures required for AutoCAD to preserve the field.
