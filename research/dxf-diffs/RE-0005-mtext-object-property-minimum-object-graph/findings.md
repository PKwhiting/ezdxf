# Findings

## Summary

The `AcObjProp Length` field shows the same repair pattern as the `AcVar Author` field from `RE-0004`. AutoCAD rebuilds a missing root `ACAD_FIELDLIST` dictionary entry and recreates a missing `FIELDLIST` object, but it does not rebuild the host `MTEXT` `ACAD_XDICTIONARY` link. Without that host link, the object-backed field graph is effectively lost even though display text remains.

## Confirmed Changes

1. Removing only the root `ACAD_FIELDLIST` dictionary entry is repairable.
2. Removing the entire `FIELDLIST` object is also repairable.
3. In both repairable cases, AutoCAD restored the host `MTEXT` xdictionary and kept the visible evaluated text `10.0000`.
4. Removing the host `MTEXT` `ACAD_XDICTIONARY` block is not repairable.
5. In the `no-mtext-xdict` roundtrip, the host `MTEXT` remains plain text `10.0000` with no xdictionary restored.
6. In the `no-mtext-xdict` roundtrip, there is no surviving `AcObjProp` field object or `ACAD_FIELD` dictionary entry.
7. The `FIELDLIST` class/root structures may still remain without a working host link, so they are not sufficient by themselves.

## Key Excerpts

Missing root fieldlist entry was restored by AutoCAD:

    2084: ACAD_FIELDLIST
    2085: 350
    2086: B3

Missing `FIELDLIST` object was recreated by AutoCAD:

    2250: FIELDLIST
    2261: 100
    2262: AcDbIdSet
    2270: AcDbFieldList

Host `MTEXT` xdictionary survives in repairable variants:

    2018: {ACAD_XDICTIONARY
    2050: 10.0000

Host `MTEXT` xdictionary is not restored when removed:

    2014: MTEXT
    2015:   5
    2016: 90
    2017: 330
    ...
    2044: 10.0000

No surviving `AcObjProp` field object after removing host xdictionary:

- `roundtrip-no-mtext-xdict/before.dxf` contains no `AcObjProp`
- `roundtrip-no-mtext-xdict/before.dxf` contains no `Length`
- `roundtrip-no-mtext-xdict/before.dxf` contains no `_ObjIdx`

## Interpretation

- The host `MTEXT` extension dictionary link is again the critical anchor for object-backed field storage.
- `FIELDLIST` is reconstructible and therefore likely not the minimum required authored structure.
- The same structural rule appears to hold for both variable fields and object-property fields.
- That strongly suggests `ezdxf` should prioritize correct host xdictionary plus `ACAD_FIELD` subtree authoring above `FIELDLIST` completeness.

## Likely ezdxf Targets

- src/ezdxf/entities/dxfobj.py
- src/ezdxf/entities/idbuffer.py
- src/ezdxf/entities/mtext.py

## Non-Goals From This Experiment

- proving that these three variants exhaust the minimum graph question
- determining whether the parent `_text` wrapper field is required
- determining whether explicit object references inside the child field can be reduced further
