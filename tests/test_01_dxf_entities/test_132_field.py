# Copyright (c) 2026, Manfred Moitzi
# License: MIT License
from typing import cast
import io
import ezdxf
import pytest

from ezdxf.entities.dxfobj import Field
from ezdxf.entities.mtext import MText
from ezdxf.lldxf.tagwriter import TagCollector, basic_tags_from_text

FIELD = """0
FIELD
5
0
330
0
100
AcDbField
1
AcVar
2
\\AcVar Author
90
0
301
----
98
4
"""

FIELD_WITH_OVERFLOW = """0
FIELD
5
0
330
0
100
AcDbField
1
AcExpr
2
abc
3
def
90
1
"""


@pytest.fixture
def entity():
    return Field.from_text(FIELD)


def test_registered():
    from ezdxf.entities.factory import ENTITY_CLASSES

    assert "FIELD" in ENTITY_CLASSES


def test_default_init():
    field = Field()
    assert field.dxftype() == "FIELD"
    assert field.dxf.handle is None
    assert field.dxf.owner is None
    assert len(field.tags) == 0


def test_default_new():
    field = Field.new(handle="ABBA", owner="0", dxfattribs={})
    assert field.dxf.n_child_fields is None
    assert len(field.tags) == 0


def test_load_from_text(entity):
    assert entity.evaluator_id == "AcVar"
    assert entity.field_code == "\\AcVar Author"
    assert entity.dxf.n_child_fields == 0


def test_write_dxf():
    entity = Field.from_text(FIELD)
    result = TagCollector.dxftags(entity)
    expected = basic_tags_from_text(FIELD)
    assert result == expected


def test_field_code_overflow():
    entity = Field.from_text(FIELD_WITH_OVERFLOW)
    assert entity.evaluator_id == "AcExpr"
    assert entity.field_code == "abcdef"
    assert entity.dxf.n_child_fields == 1


def test_reset_tags_updates_simple_attributes():
    entity = Field()
    entity.reset([(1, "AcVar"), (2, "\\AcVar Login"), (90, 0)])
    assert entity.evaluator_id == "AcVar"
    assert entity.field_code == "\\AcVar Login"
    assert entity.dxf.n_child_fields == 0


def test_reset_strips_leading_subclass_marker():
    entity = Field()
    entity.reset([(100, "AcDbField"), (1, "AcVar"), (2, "\\AcVar Login")])
    assert entity.tags[0] == (1, "AcVar")
    tags = TagCollector.dxftags(entity)
    assert (100, "AcDbField") in tags


def test_child_and_object_handles_from_tags():
    entity = Field()
    entity.reset(
        [
            (1, "_text"),
            (2, "%<\\_FldIdx 0>%"),
            (360, "A1"),
            (360, "A2"),
            (331, "B1"),
        ]
    )
    assert entity.is_text_wrapper is True
    assert entity.child_handles == ["A1", "A2"]
    assert entity.object_handles == ["B1"]


def test_set_text_wrapper_builds_minimal_wrapper_tags():
    child = Field.new(handle="ABBA", owner="0", dxfattribs={})
    wrapper = Field()
    wrapper.set_text_wrapper(child)
    assert wrapper.is_text_wrapper is True
    assert wrapper.field_code == "%<\\_FldIdx 0>%"
    assert wrapper.child_handles == ["ABBA"]
    assert (6, "ACFD_FIELDTEXT_CHECKSUM") in wrapper.tags
    assert (7, "ACFD_FIELD_VALUE") in wrapper.tags
    assert (301, "") in wrapper.tags


def test_set_acvar_builds_minimal_child_field():
    field = Field()
    field.set_acvar("Author", display="----")
    assert field.evaluator_id == "AcVar"
    assert field.field_code == "\\AcVar Author"
    assert field.dxf.n_child_fields == 0
    assert (6, "Variable") in field.tags
    assert (1, "Author") in field.tags
    assert (301, "----") in field.tags


def test_set_acobjprop_builds_object_property_field():
    field = Field()
    field.set_acobjprop("ABBA", "Length", value=10.0, display="10.0000")
    assert field.evaluator_id == "AcObjProp"
    assert field.field_code == "\\AcObjProp Object(%<\\_ObjIdx 0>%).Length \\f \"%lu2\""
    assert field.object_handles == ["ABBA"]
    assert (6, "ObjectPropertyName") in field.tags
    assert (1, "Length") in field.tags
    assert (301, "10.0000") in field.tags


def test_clear_tags_clears_simple_attributes():
    entity = Field.from_text(FIELD)
    entity.clear()
    assert len(entity.tags) == 0
    assert entity.evaluator_id == ""
    assert entity.field_code == ""
    assert entity.dxf.n_child_fields is None


def test_add_field_to_objects_section():
    doc = ezdxf.new("R2007")
    field = cast(Field, doc.objects.add_field(owner="ABBA"))
    assert field.dxftype() == "FIELD"
    assert field.dxf.owner == "ABBA"


def test_minimal_export_from_dxfattribs():
    doc = ezdxf.new("R2007")
    field = cast(
        Field,
        doc.objects.add_field(
            owner="ABBA",
            dxfattribs={
                "evaluator_id": "AcVar",
                "field_code": "\\AcVar Author",
                "n_child_fields": 0,
            },
        ),
    )
    tags = TagCollector.dxftags(field)
    assert (1, "AcVar") in tags
    assert (2, "\\AcVar Author") in tags


def test_writing_document_adds_field_class_definition():
    doc = ezdxf.new("R2007")
    cast(
        Field,
        doc.objects.add_field(
            owner="ABBA",
            dxfattribs={
                "evaluator_id": "AcVar",
                "field_code": "\\AcVar Author",
                "n_child_fields": 0,
            },
        ),
    )
    stream = io.StringIO()
    doc.write(stream)
    data = stream.getvalue()
    assert "  0\nCLASS\n  1\nFIELD\n  2\nAcDbField\n" in data


def test_mtext_new_field_creates_field_dict_and_links_field():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext("TEXT")
    field = cast(
        Field,
        mtext.new_field(
            dxfattribs={
                "evaluator_id": "AcVar",
                "field_code": "\\AcVar Author",
                "n_child_fields": 0,
            }
        ),
    )
    assert isinstance(mtext, MText)
    assert mtext.has_extension_dict is True
    assert mtext.has_field_dict() is True
    field_dict = mtext.get_field_dict()
    assert field_dict.dxf.owner == mtext.get_extension_dict().handle
    assert field_dict._value_code == 360
    assert mtext.get_field() is field
    assert field.dxf.owner == field_dict.dxf.handle


def test_mtext_set_field_replaces_existing_field():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext("TEXT")
    field1 = cast(
        Field,
        mtext.new_field(
            dxfattribs={
                "evaluator_id": "AcVar",
                "field_code": "\\AcVar Author",
            }
        ),
    )
    field2 = cast(
        Field,
        doc.objects.add_field(
            dxfattribs={
                "evaluator_id": "AcVar",
                "field_code": "\\AcVar Login",
            }
        ),
    )
    mtext.set_field(field2)
    assert field1.is_alive is False
    assert mtext.get_field() is field2


def test_mtext_get_primary_field_returns_child_of_text_wrapper():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext("TEXT")
    child = cast(
        Field,
        doc.objects.add_field(
            dxfattribs={
                "evaluator_id": "AcVar",
                "field_code": "\\AcVar Author",
            }
        ),
    )
    wrapper = cast(Field, doc.objects.add_field(dxfattribs={}))
    wrapper.set_text_wrapper(child)
    mtext.set_field(wrapper)
    assert mtext.get_field() is wrapper
    assert mtext.get_primary_field() is child


def test_mtext_get_field_returns_none_without_field_dict():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext("TEXT")
    assert mtext.get_field() is None


def test_writing_mtext_field_exports_xdictionary_and_field_dict():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext("TEXT")
    mtext.new_field(
        dxfattribs={
            "evaluator_id": "AcVar",
            "field_code": "\\AcVar Author",
        }
    )
    stream = io.StringIO()
    doc.write(stream)
    data = stream.getvalue()
    assert "{ACAD_XDICTIONARY" in data
    assert "ACAD_FIELD" in data
    assert "\\AcVar Author" in data


def test_setup_field_list_creates_rootdict_entry():
    doc = ezdxf.new("R2007")
    field_list = doc.objects.setup_field_list()
    assert doc.rootdict.get("ACAD_FIELDLIST") is field_list
    assert field_list.dxf.owner == doc.rootdict.dxf.handle
    assert doc.rootdict.dxf.handle in field_list.get_reactors()
    assert field_list.dxf.flags == 2


def test_new_linked_field_creates_wrapper_and_registers_field_list():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext("TEXT")
    child, wrapper = mtext.new_linked_field(
        dxfattribs={
            "evaluator_id": "AcVar",
            "field_code": "\\AcVar Author",
        },
        text="----",
        register_field_list=True,
    )
    assert mtext.text == "----"
    assert mtext.get_field() is wrapper
    assert mtext.get_primary_field() is child
    assert child.dxf.owner == wrapper.dxf.handle
    assert mtext.get_field_dict().dxf.handle in wrapper.get_reactors()
    field_list = doc.objects.get_field_list()
    assert field_list is not None
    assert wrapper.dxf.handle in field_list.handles
    assert child.dxf.handle in field_list.handles


def test_new_acvar_field_creates_object_backed_author_field():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext("TEXT")
    child, wrapper = mtext.new_acvar_field(
        "Author", text="----", register_field_list=True
    )
    assert child.evaluator_id == "AcVar"
    assert child.field_code == "\\AcVar Author"
    assert (301, "----") in child.tags
    assert wrapper.is_text_wrapper is True
    assert mtext.get_primary_field() is child


def test_new_acobjprop_field_creates_object_backed_length_field():
    doc = ezdxf.new("R2007")
    line = doc.modelspace().add_line((0, 0), (10, 0))
    mtext = doc.modelspace().add_mtext("TEXT")
    child, wrapper = mtext.new_acobjprop_field(
        line, "Length", text=None, register_field_list=True
    )
    assert child.evaluator_id == "AcObjProp"
    assert child.object_handles == [line.dxf.handle]
    assert "Length" in child.field_code
    assert mtext.text == "10.0000"
    assert mtext.get_primary_field() is child
    field_list = doc.objects.get_field_list()
    assert field_list is not None
    assert wrapper.dxf.handle in field_list.handles
    assert child.dxf.handle in field_list.handles


def test_writing_mtext_acobjprop_field_exports_property_reference():
    doc = ezdxf.new("R2007")
    line = doc.modelspace().add_line((0, 0), (10, 0))
    mtext = doc.modelspace().add_mtext("TEXT")
    mtext.new_acobjprop_field(line, "Length", register_field_list=True)
    stream = io.StringIO()
    doc.write(stream)
    data = stream.getvalue()
    assert "AcObjProp" in data
    assert "ObjectPropertyName" in data
    assert "Length" in data


def test_graphicsfactory_add_mtext_acvar_field():
    doc = ezdxf.new("R2007")
    mtext = doc.modelspace().add_mtext_acvar_field(
        "Author", text="----", register_field_list=True
    )
    assert isinstance(mtext, MText)
    assert mtext.text == "----"
    assert mtext.get_primary_field() is not None
    assert mtext.get_primary_field().field_code == "\\AcVar Author"


def test_graphicsfactory_add_mtext_acobjprop_field():
    doc = ezdxf.new("R2007")
    line = doc.modelspace().add_line((0, 0), (10, 0))
    mtext = doc.modelspace().add_mtext_acobjprop_field(
        line, "Length", register_field_list=True
    )
    assert isinstance(mtext, MText)
    assert mtext.text == "10.0000"
    assert mtext.get_primary_field() is not None
    assert "Length" in mtext.get_primary_field().field_code


def test_new_acobjprop_field_supports_circle_radius():
    doc = ezdxf.new("R2007")
    circle = doc.modelspace().add_circle((0, 0), radius=5)
    mtext = doc.modelspace().add_mtext("TEXT")
    child, _ = mtext.new_acobjprop_field(circle, "Radius", register_field_list=True)
    assert child.evaluator_id == "AcObjProp"
    assert mtext.text == "5.0000"
    assert "Radius" in child.field_code


def test_new_acobjprop_field_supports_circle_area():
    doc = ezdxf.new("R2007")
    circle = doc.modelspace().add_circle((0, 0), radius=2)
    mtext = doc.modelspace().add_mtext("TEXT")
    child, _ = mtext.new_acobjprop_field(circle, "Area", register_field_list=True)
    assert child.evaluator_id == "AcObjProp"
    assert mtext.text == "12.5664"
    assert "Area" in child.field_code


def test_new_acobjprop_field_supports_closed_lwpolyline_area():
    doc = ezdxf.new("R2007")
    pline = doc.modelspace().add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10)], close=True
    )
    mtext = doc.modelspace().add_mtext("TEXT")
    child, _ = mtext.new_acobjprop_field(pline, "Area", register_field_list=True)
    assert child.evaluator_id == "AcObjProp"
    assert mtext.text == "100.0000"
    assert "Area" in child.field_code


def test_open_lwpolyline_area_is_not_inferred():
    doc = ezdxf.new("R2007")
    pline = doc.modelspace().add_lwpolyline([(0, 0), (10, 0), (10, 10)])
    mtext = doc.modelspace().add_mtext("TEXT")
    child, _ = mtext.new_acobjprop_field(pline, "Area", register_field_list=True)
    assert child.evaluator_id == "AcObjProp"
    assert mtext.text == "TEXT"
