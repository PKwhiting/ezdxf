# Findings

## Summary

UI-authored `MULTILEADER` object-property fields use the same overall
object-backed field graph as `MTEXT`, but the `MULTILEADER` host stores a
different `_text` wrapper shape and its child `AcObjProp` cache toggles between
two valid-looking save states on repeated AutoCAD saves.

## Confirmed Changes

1. The host `MULTILEADER` gains an extension dictionary and nested `ACAD_FIELD` dictionary.
2. AutoCAD creates a parent `_text` wrapper field and a child `AcObjProp` field referencing the target line through `331` and `330` handles.
3. The embedded `MULTILEADER` MTEXT content stores the visible text `10.0000`.
4. The `_text` wrapper uses `94 = 9`, not the `MTEXT`/`TEXT` wrapper value `13`.
5. The `_text` wrapper omits the `ACFD_FIELDTEXT_CHECKSUM` dataset entirely.
6. The embedded `MULTILEADER` MTEXT content stores color `90 = -1073741824` (`BY_LAYER`) while the outer `MULTILEADER` text color remains `92 = -1056964608` (`BY_BLOCK`).
7. The embedded `MULTILEADER` MTEXT content stores `295 = 0` (`use_word_break = 0`).
8. The first saved manual file uses the normalized child `AcObjProp` cache form (`94 = 27`, `93 = 0`, blank `302`/`301`).
9. Repeated Core Console saves oscillate the child cache between the normalized form and the populated form (`94 = 59`, `93 = 4`, `302/301 = 10.0000`).
10. A raw `ezdxf`-generated `MULTILEADER` parity file is accepted without proxy graphics; AutoCAD adds proxy graphics on the first save while preserving the normalized field graph.

## Key Excerpts

Wrapper field in the manually edited file:

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
6C
97
        0
91
       63
92
        0
94
        9
95
        2
96
        0
300

93
        0
7
ACFD_FIELD_VALUE
```

Child field in the manually edited file:

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
2F
94
       27
...
7
ACFD_FIELD_VALUE
93
        0
90
        2
140
10.0
300
%lu2
302

301

```

Embedded `MULTILEADER` MTEXT content in the manually edited file:

```text
304
10.0000
...
90
-1073741824
...
295
     0
```

## Interpretation

- `MULTILEADER` should not reuse the exact `_text` wrapper shape used by `MTEXT` and `TEXT`.
- The embedded MTEXT context for `MULTILEADER` has at least two host-specific defaults that matter for parity: `BY_LAYER` text color and `use_word_break = 0`.
- The child `AcObjProp` cache for `MULTILEADER` oscillates across repeated AutoCAD saves, so byte-level parity for that cache has to choose which valid save state to target.
- Exact proxy-graphic parity appears to be lower priority than field-graph parity, because AutoCAD will synthesize proxy graphics on the first save from a structurally valid file.

## Likely ezdxf Targets

- `src/ezdxf/entities/dxfobj.py`
- `src/ezdxf/entities/mleader.py`
- `src/ezdxf/render/mleader.py`

## Non-Goals From This Experiment

- explaining why repeated AutoCAD saves flip the child `AcObjProp` cache state
- expanding support to additional `AcObjProp` properties or entities
