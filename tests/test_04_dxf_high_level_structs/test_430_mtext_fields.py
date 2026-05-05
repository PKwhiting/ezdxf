# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
import io
import ezdxf


def test_add_mtext_acvar_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()

    mtext = msp.add_mtext_acvar_field(
        "Author",
        text="----",
        dxfattribs={"insert": (0, 0, 0)},
        register_field_list=True,
    )

    assert mtext.text == "----"
    primary = mtext.get_primary_field()
    assert primary is not None
    assert primary.evaluator_id == "AcVar"
    assert primary.field_code == "\\AcVar Author"

    field_list = doc.objects.get_field_list()
    assert field_list is not None
    assert mtext.get_field().dxf.handle in field_list.handles
    assert primary.dxf.handle in field_list.handles


def test_add_mtext_acobjprop_length_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()
    line = msp.add_line((0, 0), (10, 0))

    mtext = msp.add_mtext_acobjprop_field(
        line,
        "Length",
        dxfattribs={"insert": (0, 0, 0)},
        register_field_list=True,
    )

    assert mtext.text == "10.0000"
    primary = mtext.get_primary_field()
    assert primary is not None
    assert primary.evaluator_id == "AcObjProp"
    assert primary.object_handles == [line.dxf.handle]
    assert "Length" in primary.field_code


def test_add_mtext_acobjprop_area_field_for_closed_lwpolyline():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()
    pline = msp.add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10)], close=True
    )

    mtext = msp.add_mtext_acobjprop_field(
        pline,
        "Area",
        dxfattribs={"insert": (0, 0, 0)},
        register_field_list=True,
    )

    assert mtext.text == "100.0000"
    primary = mtext.get_primary_field()
    assert primary is not None
    assert primary.evaluator_id == "AcObjProp"
    assert "Area" in primary.field_code


def test_add_mtext_dwgprops_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()

    mtext = msp.add_mtext_dwgprops_field(
        "ProjectCode",
        text="VALUE-123",
        dxfattribs={"insert": (0, 0, 0)},
        register_field_list=True,
    )

    assert mtext.text == "VALUE-123"
    primary = mtext.get_primary_field()
    assert primary is not None
    assert primary.evaluator_id == "AcVar"
    assert primary.field_code == "\\AcVar CustomDP.ProjectCode"
    assert doc.header.custom_vars.get("ProjectCode") == "VALUE-123"


def test_writing_high_level_field_entities_exports_expected_markers():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()
    line = msp.add_line((0, 0), (10, 0))
    msp.add_mtext_acvar_field("Author", text="----", register_field_list=True)
    msp.add_mtext_acobjprop_field(line, "Length", register_field_list=True)

    stream = io.StringIO()
    doc.write(stream)
    data = stream.getvalue()
    assert "ACAD_FIELDLIST" in data
    assert "ACAD_FIELD" in data
    assert "\\AcVar Author" in data
    assert "AcObjProp" in data
