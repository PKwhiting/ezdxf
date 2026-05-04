# Notes

## Noise Observed

- AutoCAD save noise still appears in viewport, timing, and style-related sections.
- For this experiment, only the field graph repair behavior matters.

## Open Questions

1. Is the parent `_text` wrapper field required for `AcObjProp` fields?
2. Can the child `AcObjProp` field survive with fewer explicit object-reference records?
3. Is the `ACAD_FIELD` nested dictionary itself minimally required as-is?

## Recommended Follow-Up Experiments

1. Remove only the parent `_text` field wrapper from the `AcObjProp` case.
2. Remove only the child `AcObjProp` field and observe whether AutoCAD drops the field entirely.
3. Remove only explicit reference records such as `331` from the child field and roundtrip again.
