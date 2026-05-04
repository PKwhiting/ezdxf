# Findings

## Summary

The same apparent `AcVar Author` field hosted by `MTEXT` serializes very differently depending on how it is created. The AutoCAD UI creates a full object-backed field graph, while direct AutoLISP insertion leaves the field inline in the `MTEXT` text content and does not create `FIELD`, `FIELDLIST`, or `ACAD_FIELD` structures.

## Confirmed Changes

1. The AutoLISP-authored `MTEXT` stores `%<\AcVar Author>%` directly in the text tag.
2. The UI-authored `MTEXT` stores `----` as visible text instead of the field code.
3. The UI-authored version adds an extension dictionary reference to the host `MTEXT`.
4. The UI-authored version adds `FIELD` and `FIELDLIST` classes.
5. The UI-authored version adds `ACAD_FIELDLIST` and `ACAD_FIELD` dictionary entries.
6. The UI-authored version creates `FIELDLIST` and `FIELD` objects.
7. The UI-authored child field uses evaluator `AcVar` and stores `\AcVar Author` in a `FIELD` object.
8. The AutoLISP-authored version shows none of those object-backed field structures.

## Key Excerpts

AutoLISP-authored version keeps the field inline in MTEXT text:

```text
AcDbMText
...
1
%<\AcVar Author>%
```

UI-authored version replaces host text and adds xdictionary:

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
-%<\AcVar Author>%
+----
```

UI-authored version adds field graph:

```text
CLASS
1
FIELD

CLASS
1
FIELDLIST

...

3
ACAD_FIELDLIST

...

3
ACAD_FIELD
```

UI-authored child field stores the actual variable reference:

```text
100
AcDbField
1
AcVar
2
\AcVar Author
```

## Likely ezdxf Targets

- src/ezdxf/entities/dxfobj.py
- src/ezdxf/entities/idbuffer.py
- src/ezdxf/entities/mtext.py

## Interpretation

- AutoCAD supports at least two storage representations for an apparent `MTEXT` field.
- The UI path produces a canonical object-backed representation.
- Direct AutoLISP string insertion produces only an inline field-code representation.
- If the goal is AutoCAD-fidelity in `ezdxf`, object-backed field support is necessary.
- If the goal is minimal authoring support, inline field strings may still be useful for some scenarios, but they are not equivalent to UI-authored output.

## Non-Goals From This Experiment

- comparing object-property fields
- determining the minimum accepted field object graph
