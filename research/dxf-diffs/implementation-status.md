# Field Implementation Status

This note links the reverse-engineering experiments to the current `ezdxf`
implementation status for object-backed `MTEXT` fields.

## Implemented

Based on:

- `RE-0001` UI-authored `AcVar Author`
- `RE-0002` UI-authored `AcObjProp Length`
- `RE-0003` UI vs AutoLISP `AcVar Author`
- `RE-0004` minimum object graph for `AcVar`
- `RE-0005` minimum object graph for `AcObjProp`

Code support currently exists for:

- first-class `FIELD` objects
- `FIELDLIST` creation and registration
- host `MTEXT` extension-dictionary attachment
- nested `ACAD_FIELD` dictionary creation
- `_text` wrapper field creation
- object-backed `AcVar` child field creation
- object-backed `AcObjProp` child field creation

Current convenience API:

- `layout.add_mtext_acvar_field(...)`
- `layout.add_mtext_acobjprop_field(...)`
- `MText.new_acvar_field(...)`
- `MText.new_acobjprop_field(...)`

Current inferred object-property support:

- `LINE.Length`
- `CIRCLE.Radius`
- `CIRCLE.Diameter`
- `CIRCLE.Circumference`
- `CIRCLE.Area`
- closed straight-segment `LWPOLYLINE.Area`

## Confirmed by AutoCAD Roundtrip

The current generated object-backed field DXFs are accepted by AutoCAD Core
Console and can be re-saved.

Validated artifacts:

- `experiments/ezdxf-generated-fields/object_backed_author.dxf`
- `experiments/ezdxf-generated-fields/object_backed_length.dxf`
- `experiments/ezdxf-generated-fields/field_playground.dxf`

## Remaining Gaps

1. Byte-level parity with UI-authored field graphs is not guaranteed.
2. No support yet for broader `AcObjProp` property coverage.
3. No dedicated parser/authoring support yet for deeper nested field trees.
4. No public guarantee yet that the field API is stable; it should still be treated as experimental.

## Recommended Next Work

1. Expand `AcObjProp` inference selectively based on concrete reverse-engineering evidence.
2. Add one or two additional AutoCAD validation experiments for supported property cases.
3. Decide when to graduate the convenience API from experimental to supported.
