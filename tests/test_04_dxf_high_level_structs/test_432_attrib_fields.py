# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
import ezdxf


def test_attdef_new_dwgprops_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    block = doc.blocks.new("TEST")
    attdef = block.add_attdef("TAG1", insert=(0, 0), text="TEXT")

    child, wrapper = attdef.new_dwgprops_field(
        "ProjectCode", text="VALUE-123", register_field_list=True
    )

    assert attdef.dxf.text == "VALUE-123"
    assert attdef.get_field() is wrapper
    assert attdef.get_primary_field() is child
    assert child.evaluator_id == "AcVar"
    assert child.field_code == "\\AcVar CustomDP.ProjectCode"


def test_attrib_new_dwgprops_field_creates_object_backed_field():
    doc = ezdxf.new("R2007")
    block = doc.blocks.new("TEST")
    blockref = doc.modelspace().add_blockref("TEST", insert=(0, 0))
    attrib = blockref.add_attrib("TAG1", "TEXT", insert=(0, 0))

    child, wrapper = attrib.new_dwgprops_field(
        "ProjectCode", text="VALUE-123", register_field_list=True
    )

    assert attrib.dxf.text == "VALUE-123"
    assert attrib.get_field() is wrapper
    assert attrib.get_primary_field() is child
    assert child.evaluator_id == "AcVar"
    assert child.field_code == "\\AcVar CustomDP.ProjectCode"
