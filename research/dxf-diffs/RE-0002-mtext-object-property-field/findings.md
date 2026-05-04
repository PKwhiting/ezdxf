# Findings

## Summary

Adding a line-length object-property field to `MTEXT` in the AutoCAD UI creates the same high-level object-backed field structures seen in `RE-0001`, but the child field now uses the `AcObjProp` evaluator and stores both field-code text and explicit object references.

## Confirmed Changes

1. The host `MTEXT` gained an extension dictionary reference.
2. The visible `MTEXT` text changed from `FIELD_OBJECT_BASE` to the evaluated display value `10.0000`.
3. AutoCAD added `FIELD` and `FIELDLIST` class definitions.
4. AutoCAD added `ACAD_FIELDLIST` and `ACAD_FIELD` dictionary entries in the object graph.
5. AutoCAD created a `FIELDLIST` object.
6. AutoCAD created a parent `_text` field referencing one child field by `360`.
7. AutoCAD created a child `AcObjProp` field for `Length`.
8. The child field stores an explicit referenced object handle through `331` and additional object-property records through `330`.

## Key Excerpts

Host `MTEXT` gains xdictionary and evaluated display text:

```diff
 MTEXT
 5
 <REF>
+102
+{ACAD_XDICTIONARY
+360
+<REF>
+102
+}
 ...
 1
-FIELD_OBJECT_BASE
+10.0000
```

Parent `_text` field remains a wrapper around a child field index:

```text
100
AcDbField
1
_text
2
%<\_FldIdx 0>%
90
        1
360
<REF>
```

Child field uses `AcObjProp` and stores both code and explicit object references:

```text
100
AcDbField
1
AcObjProp
2
\AcObjProp Object(%<\_ObjIdx 0>%).Length \f "%lu2"
97
        1
331
<REF>
```

Object-property metadata is stored explicitly:

```text
6
ObjectPropertyId
90
       64
330
<REF>

6
ObjectPropertyName
1
Length
```

Evaluated field value is stored in the field object too:

```text
7
ACFD_FIELD_VALUE
140
10.0
300
%lu2
302
10.0000
301
10.0000
```

## Likely ezdxf Targets

- src/ezdxf/entities/dxfobj.py
- src/ezdxf/entities/idbuffer.py
- src/ezdxf/entities/mtext.py

## Interpretation

- UI-authored object-property fields are object-backed, just like UI-authored variable fields.
- The host `MTEXT` stores the evaluated display string, not the authoritative field expression.
- The authoritative field expression is stored in a child `FIELD` object using the `AcObjProp` evaluator.
- Unlike the variable-field case, object-property fields also store explicit referenced object handles (`331`, and a related `330` record in the object-property payload).
- This means `ezdxf` field support likely needs both:
  - the field-code text model
  - the explicit object-reference model

## Non-Goals From This Experiment

- proving a creation API in `ezdxf`
- determining whether a reduced object graph would still be accepted by AutoCAD
