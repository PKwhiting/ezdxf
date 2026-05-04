# Findings

## Summary

AutoCAD can repair some missing field-related structures on load/save, but not all of them. Specifically, AutoCAD rebuilds a missing root `ACAD_FIELDLIST` dictionary entry and recreates a missing `FIELDLIST` object, but it does not rebuild the host `MTEXT` `ACAD_XDICTIONARY` link. Without that host link, the object-backed field graph is effectively lost.

## Confirmed Changes

1. Removing only the root `ACAD_FIELDLIST` dictionary entry is repairable.
2. Removing the entire `FIELDLIST` object is also repairable.
3. In both repairable cases, AutoCAD restored the host `MTEXT` xdictionary and kept the visible placeholder text `----`.
4. Removing the host `MTEXT` `ACAD_XDICTIONARY` block is not repairable.
5. In the `no-mtext-xdict` roundtrip, the host `MTEXT` remains plain text `----` with no xdictionary restored.
6. In the `no-mtext-xdict` roundtrip, the `FIELD` objects containing `AcVar Author` are gone.
7. The `FIELDLIST` class/root structures may still remain without a working host link, so they are not sufficient by themselves.

## Key Excerpts

Missing root fieldlist entry was restored by AutoCAD:

    2058: ACAD_FIELDLIST
    2059: 350
    2060: B3

Missing `FIELDLIST` object was recreated by AutoCAD:

    2224: FIELDLIST
    2235: 100
    2236: AcDbIdSet
    2244: AcDbFieldList

Host `MTEXT` xdictionary survives in repairable variants:

    1991: 102
    1992: {ACAD_XDICTIONARY
    1993: 360
    1994: A0
    1995: 102
    1996: }
    2024: ----

Host `MTEXT` xdictionary is not restored when removed:

    1988: MTEXT
    1989:   5
    1990: 8F
    1991: 330
    ...
    2018: ----

No surviving `AcVar Author` field object after removing host xdictionary:

- `roundtrip-no-mtext-xdict/before.dxf` contains no `\AcVar Author`
- `roundtrip-no-mtext-xdict/before.dxf` contains no object `FIELD` entries beyond class metadata

## Interpretation

- The host `MTEXT` extension dictionary link is a critical part of the object-backed field graph.
- `FIELDLIST` appears to be non-critical enough for AutoCAD to reconstruct.
- The root `ACAD_FIELDLIST` dictionary entry is also reconstructible.
- Therefore, the likely minimum viable object graph is anchored by the host `MTEXT` xdictionary and its `ACAD_FIELD` subtree, not by `FIELDLIST` alone.

## Likely ezdxf Targets

- src/ezdxf/entities/dxfobj.py
- src/ezdxf/entities/idbuffer.py
- src/ezdxf/entities/mtext.py

## Non-Goals From This Experiment

- proving that the current three variants exhaust the minimum graph question
- determining whether the `_text` parent field wrapper itself is required
- determining whether `FIELDLIST` can be omitted entirely in freshly authored DXF, as opposed to repaired DXF
