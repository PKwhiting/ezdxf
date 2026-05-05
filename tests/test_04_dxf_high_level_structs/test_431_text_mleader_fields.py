# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
import ezdxf
from ezdxf.math import Vec2


def test_text_new_acvar_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    txt = doc.modelspace().add_text("TEXT")
    child, wrapper = txt.new_acvar_field("Author", text="----", register_field_list=True)

    assert txt.dxf.text == "----"
    assert txt.get_field() is wrapper
    assert txt.get_primary_field() is child
    assert child.evaluator_id == "AcVar"
    assert child.field_code == "\\AcVar Author"


def test_graphicsfactory_add_text_acobjprop_field():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()
    line = msp.add_line((0, 0), (10, 0))
    txt = msp.add_text_acobjprop_field(line, "Length", register_field_list=True)

    assert txt.dxf.text == "10.0000"
    primary = txt.get_primary_field()
    assert primary is not None
    assert primary.evaluator_id == "AcObjProp"
    assert primary.object_handles == [line.dxf.handle]


def test_text_new_dwgprops_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    txt = doc.modelspace().add_text("TEXT")
    child, wrapper = txt.new_dwgprops_field(
        "ProjectCode", text="VALUE-123", register_field_list=True
    )

    assert txt.dxf.text == "VALUE-123"
    assert txt.get_field() is wrapper
    assert txt.get_primary_field() is child
    assert child.evaluator_id == "AcVar"
    assert child.field_code == "\\AcVar CustomDP.ProjectCode"


def test_graphicsfactory_add_text_dwgprops_field():
    doc = ezdxf.new("R2007")
    txt = doc.modelspace().add_text_dwgprops_field(
        "ProjectCode",
        text="VALUE-123",
        register_field_list=True,
    )
    assert txt.dxf.text == "VALUE-123"
    primary = txt.get_primary_field()
    assert primary is not None
    assert primary.field_code == "\\AcVar CustomDP.ProjectCode"
    assert doc.header.custom_vars.get("ProjectCode") == "VALUE-123"


def test_multileader_new_acvar_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()
    builder = msp.add_multileader_mtext("Standard")
    builder.set_content("TEXT")
    builder.build(insert=Vec2(0, 0))
    ml = builder.multileader

    child, wrapper = ml.new_acvar_field("Author", text="----", register_field_list=True)

    assert ml.get_mtext_content() == "----"
    assert ml.get_field() is wrapper
    assert ml.get_primary_field() is child
    assert child.evaluator_id == "AcVar"
    assert child.field_code == "\\AcVar Author"


def test_multileader_new_acobjprop_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()
    line = msp.add_line((0, 0), (10, 0))
    builder = msp.add_multileader_mtext("Standard")
    builder.set_content("TEXT")
    builder.build(insert=Vec2(0, 0))
    ml = builder.multileader

    child, wrapper = ml.new_acobjprop_field(line, "Length", register_field_list=True)

    assert ml.get_mtext_content() == "10.0000"
    assert ml.get_field() is wrapper
    assert ml.get_primary_field() is child
    assert child.evaluator_id == "AcObjProp"
    assert child.object_handles == [line.dxf.handle]
    assert (94, 27) in child.tags
    assert (6, "ACFD_FIELDTEXT_CHECKSUM") not in wrapper.tags
    assert (94, 9) in wrapper.tags


def test_multileader_new_dwgprops_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    msp = doc.modelspace()
    builder = msp.add_multileader_mtext("Standard")
    builder.set_content("TEXT")
    builder.build(insert=Vec2(0, 0))
    ml = builder.multileader

    child, wrapper = ml.new_dwgprops_field(
        "ProjectCode", text="VALUE-123", register_field_list=True
    )

    assert ml.get_mtext_content() == "VALUE-123"
    assert ml.get_field() is wrapper
    assert ml.get_primary_field() is child
    assert child.evaluator_id == "AcVar"
    assert child.field_code == "\\AcVar CustomDP.ProjectCode"
    assert doc.header.custom_vars.get("ProjectCode") == "VALUE-123"
