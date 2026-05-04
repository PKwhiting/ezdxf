# Notes

## Noise Observed

The full diff contains substantial AutoCAD save noise unrelated to the `MTEXT` field itself, including:

- viewport values
- additional dictionaries and xrecords
- table style rewrites
- visual style serialization differences
- header time values

For implementation work, focus on the host `MTEXT`, extension dictionary, `ACAD_FIELD`, `FIELDLIST`, and `FIELD` objects.

## Comparison With Scripted Inline Field Test

An earlier scripted AutoLISP test inserted this field string directly into `MTEXT`:

```text
%<\AcVar Login \f "%tc1">%
```

That run did not show obvious `FIELD`/`FIELDLIST` objects in the exported DXF. The UI-authored field in this experiment did. This suggests at least one of the following:

- inline field strings and UI-authored fields are serialized differently
- the chosen field type matters
- regeneration/evaluation state affects whether backing objects are emitted

## Recommended Follow-Up Experiments

1. `RE-0002`: MTEXT object-property field referencing a line or polyline.
2. `RE-0003`: Compare UI-authored `AcVar` field vs AutoLISP inline `AcVar` field.
3. `RE-0004`: Determine the minimal object graph required for AutoCAD to preserve the field on reload.
