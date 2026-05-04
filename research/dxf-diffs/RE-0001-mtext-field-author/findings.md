# Findings

## Summary

Adding an Author field to an `MTEXT` entity in the AutoCAD UI creates object-backed field structures. The host `MTEXT` does not store the actual field code inline as its visible text. Instead, AutoCAD adds an extension dictionary and stores field state in `OBJECTS` as `FIELDLIST` and `FIELD` objects.

## Confirmed Changes

1. The host `MTEXT` gained an extension dictionary reference.
2. The visible `MTEXT` text changed from `FIELD_BASE` to `----`.
3. AutoCAD added `FIELD` and `FIELDLIST` class definitions.
4. AutoCAD added an `ACAD_FIELDLIST` entry in the object dictionary graph.
5. AutoCAD added an `ACAD_FIELD` dictionary attached to the host entity.
6. AutoCAD created a `FIELDLIST` object referencing two field handles.
7. AutoCAD created at least two `FIELD` objects:
   - a parent `_text` field
   - a child `AcVar` field representing `Author`

## Key Excerpts

Host `MTEXT` gains xdictionary and placeholder text:

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
 330
 <REF>
 ...
 1
-FIELD_BASE
+----
```

AutoCAD adds `FIELD`/`FIELDLIST` classes:

```diff
+CLASS
+1
+FIELD
+2
+AcDbField
+...
+CLASS
+1
+FIELDLIST
+2
+AcDbFieldList
```

Object dictionary graph gains field-related entries:

```diff
 3
+ACAD_FIELDLIST
+350
+<REF>
 ...
+DICTIONARY
+...
+3
+ACAD_FIELD
+360
+<REF>
```

`FIELDLIST` object stores multiple field handles:

```diff
+FIELDLIST
+5
+<REF>
+...
+100
+AcDbIdSet
+90
+        2
+330
+<REF>
+330
+<REF>
+100
+AcDbFieldList
```

Parent `_text` field points to child field by `360`:

```diff
+FIELD
+...
+100
+AcDbField
+1
+_text
+2
+%<\_FldIdx 0>%
+90
+        1
+360
+<REF>
```

Child field stores the actual variable reference:

```diff
+FIELD
+...
+100
+AcDbField
+1
+AcVar
+2
+\AcVar Author
+...
+301
+----
```

## Interpretation

- UI-authored `MTEXT` fields are object-backed.
- The host `MTEXT` text content is a display placeholder, not the authoritative field code.
- The authoritative field code is stored in `FIELD` objects under an `ACAD_FIELD` dictionary, reachable from the host entity extension dictionary.
- `FIELDLIST` appears to manage field membership/order for the host.

## Likely ezdxf Targets

- `src/ezdxf/entities/dxfobj.py`
  - implement `Field`
- `src/ezdxf/entities/idbuffer.py`
  - extend or reuse `FieldList`
- `src/ezdxf/entities/mtext.py`
  - add a host-side API for field attachment and preservation

## Non-Goals From This Experiment

- This experiment does not establish the exact creation API for object-property fields.
- This experiment does not prove whether every AutoLISP-created field string produces the same object graph.
- This experiment does not identify the minimum subset of objects required for AutoCAD to accept an authored field.
