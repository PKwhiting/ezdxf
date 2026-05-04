# Notes

## Noise Observed

- AutoCAD save noise still appears in viewport, timing, and style-related sections.
- For this experiment, only the field graph repair behavior matters.

## Open Questions

1. Is the parent `_text` field wrapper required, or can a child `AcVar`/`AcObjProp` field be attached directly?
2. Is the nested `ACAD_FIELD` dictionary required as-is, or can its structure be simplified?
3. Can `FIELDLIST` be omitted entirely in newly authored DXF if the host xdictionary and field objects are correct?

## Recommended Follow-Up Experiments

1. Remove only the parent `_text` field and test whether AutoCAD rebuilds it.
2. Remove only the child `AcVar` field and observe whether AutoCAD drops the field entirely.
3. Perform the same reduction sequence on the `AcObjProp Length` object-property field from `RE-0002`.
