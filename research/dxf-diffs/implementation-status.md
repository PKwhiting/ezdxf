# Field Implementation Status

This note links the reverse-engineering experiments to the current `ezdxf`
implementation status for object-backed fields.

## Implemented

Based on:

- `RE-0001` UI-authored `AcVar Author`
- `RE-0002` UI-authored `AcObjProp Length`
- `RE-0003` UI vs AutoLISP `AcVar Author`
- `RE-0004` minimum object graph for `AcVar`
- `RE-0005` minimum object graph for `AcObjProp`
- `RE-0006` UI-authored `DWGPROPS Title`
- `RE-0007` UI-authored custom `DWGPROPS ProjectCode`
- `RE-0008` UI-authored `MULTILEADER` object-property field

Code support currently exists for:

- first-class `FIELD` objects
- `FIELDLIST` creation and registration
- host extension-dictionary attachment for `MTEXT`, `TEXT`, `MULTILEADER`,
  `ATTDEF`, and `ATTRIB`
- nested `ACAD_FIELD` dictionary creation
- `_text` wrapper field creation
- object-backed `AcVar` child field creation
- object-backed `DWGPROPS` child field creation
- object-backed `AcObjProp` child field creation
- `INSERT.add_attrib_*_field(...)` convenience wrappers

Current convenience API:

- `layout.add_mtext_acvar_field(...)`
- `layout.add_mtext_dwgprops_field(...)`
- `layout.add_mtext_acobjprop_field(...)`
- `layout.add_text_acvar_field(...)`
- `layout.add_text_dwgprops_field(...)`
- `layout.add_text_acobjprop_field(...)`
- `layout.add_attdef_acvar_field(...)`
- `layout.add_attdef_dwgprops_field(...)`
- `layout.add_attdef_acobjprop_field(...)`

Current inferred object-property support:

- `LINE.Length`
- `ELLIPSE.MajorRadius`
- `ELLIPSE.MinorRadius`
- `ELLIPSE.Area`
- `ARC.Radius`
- `ARC.Length`
- `ARC.ArcLength`
- `ARC.Area`
- straight-segment `LWPOLYLINE.Length`
- `CIRCLE.Radius`
- `CIRCLE.Diameter`
- `CIRCLE.Circumference`
- `CIRCLE.Area`
- closed straight-segment `LWPOLYLINE.Area`

## Confirmed by AutoCAD Roundtrip

The current generated object-backed field DXFs are accepted by AutoCAD Core
Console and can be re-saved.

The current wrapper-field checksum now follows the visible host text, which
stabilizes the minimal `MTEXT`/`TEXT` object-property roundtrip.

`MULTILEADER` host fidelity also improved based on the new UI-authored
baseline: the wrapper now uses `94 = 9`, omits the checksum dataset, and the
embedded MTEXT content now uses the observed `BY_LAYER` text color and
`use_word_break = 0` defaults.

The current raw `MULTILEADER` output can omit proxy graphics and still be
accepted by AutoCAD; AutoCAD synthesizes proxy graphics on the first save.

`MULTILEADER` still has one unresolved roundtrip difference for
object-property fields: AutoCAD oscillates the cached child-field value
metadata across repeated saves (`94: 59 <-> 27`, `93: 4 <-> 0`, and
populated/blank `302`/`301` display strings), even though the field graph
itself survives.

Validated artifacts:

- `experiments/ezdxf-generated-fields/object_backed_author.dxf`
- `experiments/ezdxf-generated-fields/object_backed_length.dxf`
- `experiments/ezdxf-generated-fields/field_playground.dxf`
- `experiments/ezdxf-generated-fields/field_hosts_validation.dxf`
- `experiments/ezdxf-generated-fields/dwgprops_hosts_validation.dxf`
- `experiments/ezdxf-generated-fields/all_supported_fields_validation.dxf`
- `experiments/ezdxf-generated-fields/all_supported_field_flows_validation.dxf`

## Remaining Gaps

1. Byte-level parity with UI-authored field graphs is not guaranteed.
2. `MULTILEADER` `AcObjProp` cache behavior is still not stable across repeated saves.
3. `AcObjProp` property coverage is still intentionally narrow.
4. No dedicated parser/authoring support yet for deeper nested field trees.
5. No public guarantee yet that the field API is stable; it should still be treated as experimental.

## Recommended Next Work

1. Investigate why repeated AutoCAD saves flip the `MULTILEADER` child `AcObjProp` cache state.
2. Expand `AcObjProp` inference selectively based on concrete reverse-engineering evidence.
3. Decide when to graduate the convenience API from experimental to supported.
