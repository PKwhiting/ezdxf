# Findings

## Summary

The UI-authored DWGPROPS `Title` field for an `MTEXT` host uses the same object-backed field graph pattern as previous MTEXT field experiments. The child field evaluator is still `AcVar`, but the field code is stored as `\AcVar CustomDP.Title \f "%tc1"`, indicating that drawing properties are represented through the `CustomDP.*` namespace rather than a separate evaluator family.

## Confirmed Changes

1. The host `MTEXT` gained an `ACAD_XDICTIONARY` reference and an `ACAD_FIELD` nested dictionary.
2. AutoCAD created the usual `_text` wrapper `FIELD` and a child `FIELD` object.
3. The child field evaluator is `AcVar`.
4. The child field code is `\AcVar CustomDP.Title \f "%tc1"`.
5. The visible MTEXT content became `VALUE-HERE FOR TESTING`.
6. The child field stored both a property token `CustomDP.Title` and the evaluated display string.

## Key Excerpts

Host MTEXT stores the displayed value and field dictionary link:

```text
2056: MTEXT
2059: 102
2060: {ACAD_XDICTIONARY
...
2089:   1
2090: VALUE-HERE FOR TESTING
```

The wrapper field remains the standard `_text` form:

```text
10504: AcDbField
10506: _text
10508: %<\_FldIdx 0>%
```

The child field is still `AcVar`, but uses the drawing-property namespace:

```text
10586: AcDbField
10588: AcVar
10590: \AcVar CustomDP.Title \f "%tc1"
10616: CustomDP.Title
10626: ACFD_FIELD_VALUE
```

The evaluated value is stored in the child field payload:

```text
10638: VALUE-HERE FOR TESTING
10642: VALUE-HERE FOR TESTING
```

## Interpretation

- DWGPROPS-backed title fields are not a new field evaluator family.
- At least for `Title`, AutoCAD represents the field as an `AcVar` child field.
- The distinguishing part is the field code namespace: `CustomDP.Title`.
- This suggests the next `ezdxf` authoring step is likely a convenience API on top of `AcVar` rather than a wholly new `FIELD` payload family.

## Likely ezdxf Targets

- src/ezdxf/entities/dxfobj.py
- src/ezdxf/entities/mtext.py
- src/ezdxf/entities/text.py
- src/ezdxf/entities/mleader.py
- src/ezdxf/graphicsfactory.py

## Non-Goals From This Experiment

- determining whether every standard drawing property uses the `CustomDP.*` namespace
- determining whether custom DWGPROPS fields differ from `Title`
- extending support to TEXT or MULTILEADER for this field family
