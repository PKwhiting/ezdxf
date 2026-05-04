# Experiment Index

| ID | Title | Status | Host | AutoCAD | Key Result | ezdxf Targets |
| --- | --- | --- | --- | --- | --- | --- |
| RE-0001 | MTEXT field author | analyzed | MTEXT | 2026 / 2018 DXF | UI-authored MTEXT field is backed by extension dictionary, `ACAD_FIELD`, `FIELDLIST`, and `FIELD` objects | `src/ezdxf/entities/dxfobj.py`, `src/ezdxf/entities/idbuffer.py`, `src/ezdxf/entities/mtext.py` |
| RE-0002 | MTEXT object property field | analyzed | MTEXT | AutoCAD 2026 | UI-authored object-property field is object-backed and stores both an inline `AcObjProp` field code and explicit object references (`331`/`330`) | `src/ezdxf/entities/dxfobj.py`, `src/ezdxf/entities/idbuffer.py`, `src/ezdxf/entities/mtext.py` |
| RE-0003 | MTEXT UI vs AutoLISP AcVar field | analyzed | MTEXT | AutoCAD 2026 | UI-authored `AcVar Author` field is object-backed; AutoLISP-authored version stays inline in MTEXT text with no `FIELD` graph | `src/ezdxf/entities/dxfobj.py`, `src/ezdxf/entities/idbuffer.py`, `src/ezdxf/entities/mtext.py` |
| RE-0004 | MTEXT field minimum object graph | analyzed | MTEXT | AutoCAD 2026 | `ACAD_FIELDLIST` root entry and `FIELDLIST` object are repairable; host `MTEXT` xdictionary is critical and not auto-rebuilt | `src/ezdxf/entities/dxfobj.py`, `src/ezdxf/entities/idbuffer.py`, `src/ezdxf/entities/mtext.py` |
| RE-0005 | MTEXT object-property minimum object graph | analyzed | MTEXT | AutoCAD 2026 | `ACAD_FIELDLIST` root entry and `FIELDLIST` object are repairable; host `MTEXT` xdictionary is critical and not auto-rebuilt for `AcObjProp` fields either | `src/ezdxf/entities/dxfobj.py`, `src/ezdxf/entities/idbuffer.py`, `src/ezdxf/entities/mtext.py` |
