# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
"""Create MTEXT fields with the experimental object-backed field API.

This example shows:

- drawing-variable fields via ``add_mtext_acvar_field()``
- object-property fields via ``add_mtext_acobjprop_field()``

The generated DXF file is meant for inspection in AutoCAD or BricsCAD.
"""
from __future__ import annotations

from pathlib import Path
import ezdxf

OUT = Path("~/Desktop/Outbox").expanduser()


def build_doc() -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()

    msp.add_mtext(
        "Field API Demo",
        dxfattribs={"insert": (0, 55, 0), "char_height": 3.5, "width": 80},
    )

    msp.add_mtext(
        "Author:",
        dxfattribs={"insert": (0, 46, 0), "char_height": 2.5, "width": 20},
    )
    msp.add_mtext_acvar_field(
        "Author",
        text="----",
        dxfattribs={"insert": (24, 46, 0), "char_height": 2.5, "width": 30},
        register_field_list=True,
    )

    msp.add_text(
        "Author (TEXT):",
        height=2.5,
        dxfattribs={"insert": (60, 46, 0)},
    )
    msp.add_text_acvar_field(
        "Author",
        text="----",
        height=2.5,
        dxfattribs={"insert": (88, 46, 0)},
        register_field_list=True,
    )

    line = msp.add_line((0, 20), (10, 20))
    msp.add_mtext(
        "Line Length:",
        dxfattribs={"insert": (0, 26, 0), "char_height": 2.5, "width": 20},
    )
    msp.add_mtext_acobjprop_field(
        line,
        "Length",
        dxfattribs={"insert": (24, 26, 0), "char_height": 2.5, "width": 30},
        register_field_list=True,
    )

    polyline_length = msp.add_lwpolyline([(0, 14), (3, 18), (3, 22)])
    msp.add_mtext(
        "Polyline Length:",
        dxfattribs={"insert": (0, 32, 0), "char_height": 2.5, "width": 20},
    )
    msp.add_mtext_acobjprop_field(
        polyline_length,
        "Length",
        dxfattribs={"insert": (24, 32, 0), "char_height": 2.5, "width": 30},
        register_field_list=True,
    )

    circle = msp.add_circle((5, 8), radius=3)
    msp.add_mtext(
        "Circle Area:",
        dxfattribs={"insert": (0, 14, 0), "char_height": 2.5, "width": 20},
    )
    msp.add_mtext_acobjprop_field(
        circle,
        "Area",
        dxfattribs={"insert": (24, 14, 0), "char_height": 2.5, "width": 30},
        register_field_list=True,
    )

    polyline = msp.add_lwpolyline(
        [(0, 0), (8, 0), (8, 6), (0, 6)], close=True
    )
    msp.add_mtext(
        "Polyline Area:",
        dxfattribs={"insert": (0, 2, 0), "char_height": 2.5, "width": 20},
    )
    msp.add_mtext_acobjprop_field(
        polyline,
        "Area",
        dxfattribs={"insert": (24, 2, 0), "char_height": 2.5, "width": 30},
        register_field_list=True,
    )

    return doc


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "fields_api_demo.dxf"
    build_doc().saveas(path)
    print(f"created: {path}")
