# Copyright (c) 2019 Manfred Moitzi
# License: MIT License
import pytest
import ezdxf
from ezdxf.addons.dxf2code import (
    entities_to_code,
    table_entries_to_code,
    block_to_code,
)
from ezdxf.addons.dxf2code import (
    _fmt_mapping,
    _fmt_list,
    _fmt_api_call,
    _fmt_dxf_tags,
)


import ezdxf.entities
from ezdxf.lldxf.types import dxftag
from ezdxf.lldxf.tags import Tags  # required by exec() or eval()
from ezdxf.entities.ltype import LinetypePattern  # required by exec() or eval()
from ezdxf.math import Vec2, Vec3

doc = ezdxf.new("R2010")
msp = doc.modelspace()


def test_fmt_mapping():
    d = {"a": 1, "b": "str", "c": Vec3(), "d": "xxx \"yyy\" 'zzz'"}
    r = list(_fmt_mapping(d))
    assert r[0] == "'a': 1,"
    assert r[1] == "'b': \"str\","
    assert r[2] == "'c': (0.0, 0.0, 0.0),"
    assert r[3] == "'d': \"xxx \\\"yyy\\\" 'zzz'\","


def test_fmt_int_list():
    l = [1, 2, 3]
    r = list(_fmt_list(l))
    assert r[0] == "1,"
    assert r[1] == "2,"
    assert r[2] == "3,"


def test_fmt_float_list():
    l = [1.0, 2.0, 3.0]
    r = list(_fmt_list(l))
    assert r[0] == "1.0,"
    assert r[1] == "2.0,"
    assert r[2] == "3.0,"


def test_fmt_vector_list():
    from ezdxf.math import Vec3

    l = [Vec3(), (1.0, 2.0, 3.0)]
    r = list(_fmt_list(l))
    assert r[0] == "(0.0, 0.0, 0.0),"
    assert r[1] == "(1.0, 2.0, 3.0),"


def test_fmt_api_call():
    r = _fmt_api_call(
        "msp.add_line(",
        ["start", "end"],
        dxfattribs={"start": (0, 0), "end": (1, 0), "color": 7},
    )
    assert r[0] == "msp.add_line("
    assert r[1] == "    start=(0, 0),"
    assert r[2] == "    end=(1, 0),"
    assert r[3] == "    dxfattribs={"
    assert r[4] == "        'color': 7,"
    assert r[5] == "    },"
    assert r[6] == ")"


def test_fmt_dxf_tags():
    tags = [dxftag(1, "TEXT"), dxftag(10, (1, 2, 3))]
    code = "[{}]".format("".join(_fmt_dxf_tags(tags)))
    r = eval(code, globals())
    assert r == tags


def translate_to_code_and_execute(entity):
    code = entities_to_code([entity], layout="msp")
    exec(code.import_str() + "\n" + str(code), globals())
    return msp[-1]


def translate_entities_to_new_layout(entities):
    target_doc = ezdxf.new("R2010")
    return execute_entities_code_in_doc(entities, target_doc)


def execute_entities_code_in_doc(entities, target_doc):
    target_msp = target_doc.modelspace()
    namespace = {"ezdxf": ezdxf, "doc": target_doc, "msp": target_msp}
    code = entities_to_code(entities, layout="msp")
    execute_code_in_namespace(code, namespace)
    return target_doc, target_msp


def execute_code_in_namespace(code, namespace):
    exec(code.import_str() + "\n" + str(code), namespace)


def test_line_to_code():
    from ezdxf.entities.line import Line

    entity = Line.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "start": (1, 2, 3),
            "end": (4, 5, 6),
        },
    )

    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "start", "end"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_point_to_code():
    from ezdxf.entities.point import Point

    entity = Point.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "location": (1, 2, 3),
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "location"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_circle_to_code():
    from ezdxf.entities.circle import Circle

    entity = Circle.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "center": (1, 2, 3),
            "radius": 2,
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "center", "radius"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_arc_to_code():
    from ezdxf.entities.arc import Arc

    entity = Arc.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "center": (1, 2, 3),
            "radius": 2,
            "start_angle": 30,
            "end_angle": 60,
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "center", "radius", "start_angle", "end_angle"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_text_to_code():
    from ezdxf.entities.text import Text

    entity = Text.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "text": "xyz",
            "insert": (2, 3, 4),
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "text", "insert"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_solid_to_code():
    from ezdxf.entities.solid import Solid

    entity = Solid.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "vtx0": (1, 2, 3),
            "vtx1": (4, 5, 6),
            "vtx2": (7, 8, 9),
            "vtx3": (3, 2, 1),
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("vtx0", "vtx1", "vtx2", "vtx3"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_shape_to_code():
    from ezdxf.entities.shape import Shape

    entity = Shape.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "name": "shape_name",
            "insert": (2, 3, 4),
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "name", "insert"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_ellipse_to_code():
    from ezdxf.entities.ellipse import Ellipse

    entity = Ellipse.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "center": (1, 2, 3),
            "major_axis": (2, 0, 0),
            "ratio": 0.5,
            "start_param": 1,
            "end_param": 3,
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in (
        "color",
        "center",
        "major_axis",
        "ratio",
        "start_param",
        "end_param",
    ):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_insert_to_code():
    from ezdxf.entities.insert import Insert

    entity = Insert.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "name": "block1",
            "insert": (2, 3, 4),
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("name", "insert"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_insert_with_attrib_to_code():
    source_doc = ezdxf.new("R2010")
    source_doc.blocks.new("ATTRIB_BLOCK")
    source_msp = source_doc.modelspace()
    insert = source_msp.add_blockref("ATTRIB_BLOCK", (2, 3, 4))
    insert.add_attrib("TAG1", "Text1", (5, 6, 7))

    _, new_msp = translate_entities_to_new_layout([insert])
    new_insert = next(entity for entity in new_msp if entity.dxftype() == "INSERT")

    assert len(new_insert.attribs) == 1
    assert len([entity for entity in new_msp if entity.dxftype() == "ATTRIB"]) == 0
    assert new_insert.attribs[0].dxf.tag == "TAG1"
    assert new_insert.attribs[0].dxf.text == "Text1"


def test_attdef_to_code():
    from ezdxf.entities.attrib import AttDef

    entity = AttDef.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "tag": "TAG1",
            "text": "Text1",
            "insert": (2, 3, 4),
        },
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("tag", "text", "insert"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)


def test_mtext_to_code():
    from ezdxf.entities.mtext import MText

    entity = MText.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "insert": (2, 3, 4),
        },
    )
    text = "xxx \"yyy\" 'zzz'"
    entity.text = text
    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "insert"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)
    assert new_entity.text == "xxx \"yyy\" 'zzz'"


def test_lwpolyline_to_code():
    from ezdxf.entities.lwpolyline import LWPolyline

    entity = LWPolyline.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
        },
    )
    entity.set_points(
        [
            (1, 2, 0, 0, 0),
            (4, 3, 0, 0, 0),
            (7, 8, 0, 0, 0),
        ]
    )
    new_entity = translate_to_code_and_execute(entity)
    for name in ("color", "count"):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)
    for np, ep in zip(new_entity.get_points(), entity.get_points()):
        assert np == ep


def test_polyline_to_code():
    # POLYLINE does not work without an entity space
    polyline = msp.add_polyline3d(
        [
            (1, 2, 3),
            (2, 3, 7),
            (9, 3, 1),
            (4, 4, 4),
            (0, 5, 8),
        ]
    )

    new_entity = translate_to_code_and_execute(polyline)
    # Are the last two entities POLYLINE entities?
    assert msp[-2].dxftype() == msp[-1].dxftype()
    assert len(new_entity) == len(polyline)
    assert new_entity.dxf.flags == polyline.dxf.flags
    for np, ep in zip(new_entity.points(), polyline.points()):
        assert np == ep


def cmp_vertices(a, b):
    return all(Vec3(v0).isclose(v1) for v0, v1 in zip(a, b))


def test_spline_to_code():
    from ezdxf.entities.spline import Spline

    entity = Spline.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
            "degree": 3,
        },
    )
    entity.fit_points = [(1, 2, 0), (4, 3, 0), (7, 8, 0)]
    entity.control_points = [(1, 2, 0), (4, 3, 0), (7, 8, 0)]
    entity.knots = [1, 2, 3, 4, 5, 6, 7]
    entity.weights = [1.0, 2.0, 3.0]
    new_entity = translate_to_code_and_execute(entity)
    for name in (
        "color",
        "n_knots",
        "n_control_points",
        "n_fit_points",
        "degree",
    ):
        assert new_entity.get_dxf_attrib(name) == entity.get_dxf_attrib(name)

    assert new_entity.knots == entity.knots
    assert cmp_vertices(new_entity.control_points, entity.control_points) is True
    assert cmp_vertices(new_entity.fit_points, entity.fit_points) is True
    assert new_entity.weights == entity.weights


def test_leader_to_code():
    from ezdxf.entities.leader import Leader

    entity = Leader.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
        },
    )
    entity.set_vertices(
        [
            (1, 2, 0),
            (4, 3, 0),
            (7, 8, 0),
        ]
    )
    new_entity = translate_to_code_and_execute(entity)
    assert new_entity.dxf.color == entity.dxf.color
    for np, ep in zip(new_entity.vertices, entity.vertices):
        assert np == ep


def test_mesh_to_code():
    from ezdxf.entities.mesh import Mesh
    from ezdxf.render.forms import cube

    entity = Mesh.new(
        handle="ABBA",
        owner="0",
        dxfattribs={
            "color": "7",
        },
    )
    c = cube()
    entity.vertices = c.vertices
    entity.faces = c.faces

    assert len(entity.vertices) == 8
    new_entity = translate_to_code_and_execute(entity)
    assert cmp_vertices(entity.vertices, new_entity.vertices) is True
    assert list(entity.faces) == list(new_entity.faces)


def test_layer_entry():
    from ezdxf.entities.layer import Layer

    layer = Layer.new("LAYER", dxfattribs={"name": "TestTest", "color": 3})
    code = table_entries_to_code([layer], drawing="doc")
    exec(str(code), globals())
    layer = doc.layers.get("TestTest")
    assert layer.dxf.color == 3


def test_ltype_entry():
    from ezdxf.entities.ltype import Linetype

    ltype = Linetype.new(
        "FFFF",
        dxfattribs={
            "name": "TEST",
            "description": "TESTDESC",
        },
    )
    ltype.setup_pattern([0.2, 0.1, -0.1])
    code = table_entries_to_code([ltype], drawing="doc")
    exec(str(code), globals())
    new_ltype = doc.linetypes.get("TEST")
    assert new_ltype.dxf.description == ltype.dxf.description
    assert new_ltype.pattern_tags.tags == ltype.pattern_tags.tags
    # all imports added
    assert any(line.endswith("Tags") for line in code.imports)
    assert any(line.endswith("dxftag") for line in code.imports)
    assert any(line.endswith("LinetypePattern") for line in code.imports)


def test_mleaderstyle_entry():
    source_doc = ezdxf.new("R2010")
    style = source_doc.mleader_styles.duplicate_entry("Standard", "TEST_STYLE")
    style.dxf.default_text_content = "STYLE_TEXT"
    style.dxf.char_height = 3.5
    style.set_arrow_head("DOT")

    target_doc = ezdxf.new("R2010")
    namespace = {"ezdxf": ezdxf, "doc": target_doc}
    code = table_entries_to_code([style], drawing="doc")
    execute_code_in_namespace(code, namespace)
    new_style = target_doc.mleader_styles.get("TEST_STYLE")

    assert new_style is not None
    assert new_style.dxf.default_text_content == "STYLE_TEXT"
    assert new_style.dxf.char_height == 3.5
    assert target_doc.entitydb.get(new_style.dxf.arrow_head_handle).dxf.name == "_DOT"


def test_mleaderstyle_entry_missing_block_handle_is_safe():
    source_doc = ezdxf.new("R2010")
    style = source_doc.mleader_styles.duplicate_entry("Standard", "TEST_STYLE")
    source_doc.blocks.new("STYLE_BLOCK")
    style.dxf.block_record_handle = source_doc.blocks.get(
        "STYLE_BLOCK"
    ).block_record_handle

    target_doc = ezdxf.new("R2010")
    namespace = {"ezdxf": ezdxf, "doc": target_doc}
    code = table_entries_to_code([style], drawing="doc")
    execute_code_in_namespace(code, namespace)
    new_style = target_doc.mleader_styles.get("TEST_STYLE")

    assert new_style is not None
    assert new_style.dxf.hasattr("block_record_handle") is False


def test_block_to_code():
    testdoc = ezdxf.new()
    block = testdoc.blocks.new("TestBlock", dxfattribs={"description": "test"})
    block.add_line((1, 1), (2, 2))
    code = block_to_code(block, drawing="doc")
    exec(str(code), globals())
    new_block = doc.blocks.get("TestBlock")
    assert new_block.block.dxf.description == block.block.dxf.description
    assert new_block[0].dxftype() == block[0].dxftype()


def test_hatch_to_code():
    from ezdxf.entities import Hatch

    hatch = Hatch()
    hatch.set_pattern_fill(name="ANGLE")
    hatch.paths.add_polyline_path(
        [(0, 0), (100, 0), (100, 100), (0, 100)], is_closed=True
    )

    new_hatch = translate_to_code_and_execute(hatch)
    assert isinstance(new_hatch, Hatch)
    assert new_hatch.has_pattern_fill
    assert len(new_hatch.pattern.lines) == len(hatch.pattern.lines)


def test_text_field_to_code():
    source_doc = ezdxf.new("R2010")
    source_msp = source_doc.modelspace()
    text = source_msp.add_text("----")
    child, _ = text.new_acvar_field(
        "Author", text="----", register_field_list=True
    )

    new_doc, new_msp = translate_entities_to_new_layout([text])
    new_text = new_msp[-1]
    new_child = new_text.get_primary_field("TEXT")

    assert new_text.dxf.text == text.dxf.text
    assert new_child.field_code == child.field_code
    assert new_doc.objects.get_field_list() is not None


def test_mtext_object_property_field_to_code():
    source_doc = ezdxf.new("R2010")
    source_msp = source_doc.modelspace()
    line = source_msp.add_line((0, 0), (2, 0))
    mtext = source_msp.add_mtext("0")
    child, _ = mtext.new_acobjprop_field(
        line, "Length", register_field_list=True
    )

    _, new_msp = translate_entities_to_new_layout([line, mtext])
    new_line = new_msp[0]
    new_mtext = new_msp[1]
    new_child = new_mtext.get_primary_field("TEXT")

    assert new_child.field_code == child.field_code
    assert new_child.object_handles == [new_line.dxf.handle]


def test_insert_attrib_field_to_code():
    source_doc = ezdxf.new("R2010")
    source_msp = source_doc.modelspace()
    insert = source_msp.add_blockref("TEST", (0, 0))
    attrib = insert.add_attrib("TAG", "VALUE", (0, 0))
    child, _ = attrib.new_dwgprops_field(
        "ProjectCode",
        value="VALUE-123",
        text="VALUE-123",
        register_field_list=True,
    )

    new_doc, new_msp = translate_entities_to_new_layout([insert])
    new_insert = next(entity for entity in new_msp if entity.dxftype() == "INSERT")
    new_attrib = new_insert.attribs[0]
    new_child = new_attrib.get_primary_field("TEXT")

    assert new_child.field_code == child.field_code
    assert new_doc.header.custom_vars.get("ProjectCode") == "VALUE-123"


def test_multileader_mtext_to_code():
    from ezdxf.render.mleader import ConnectionSide, TextAlignment

    source_doc = ezdxf.new("R2010")
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext()
    builder.set_content(
        "note", color=3, char_height=2.5, alignment=TextAlignment.right
    )
    builder.set_connection_properties(landing_gap=2.0, dogleg_length=4.0)
    builder.set_overall_scaling(1.25)
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))

    _, new_msp = translate_entities_to_new_layout(source_msp)
    new_ml = new_msp[-1]

    assert new_ml.dxftype() == "MULTILEADER"
    assert new_ml.context.mtext is not None
    assert new_ml.context.mtext.default_content == "note"
    assert new_ml.context.mtext.alignment == 3
    assert new_ml.context.char_height == builder.multileader.context.char_height
    assert len(new_ml.context.leaders) == 1
    assert len(new_ml.context.leaders[0].lines) == 1
    assert cmp_vertices(
        new_ml.context.leaders[0].lines[0].vertices,
        builder.multileader.context.leaders[0].lines[0].vertices,
    ) is True
    assert len(list(new_ml.virtual_entities())) == len(
        list(builder.multileader.virtual_entities())
    )


def test_multileader_field_to_code():
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext()
    child, _ = builder.set_acvar_field(
        "Author", text="----", register_field_list=True
    )
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))

    new_doc, new_msp = translate_entities_to_new_layout(source_msp)
    new_ml = new_msp[-1]
    new_child = new_ml.get_primary_field("TEXT")

    assert new_ml.context.mtext is not None
    assert new_ml.context.mtext.default_content == "----"
    assert new_child is not None
    assert new_child.field_code == child.field_code
    assert new_doc.objects.get_field_list() is not None


def test_multileader_custom_style_to_code():
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    style = source_doc.mleader_styles.duplicate_entry("Standard", "MY_STYLE")
    style.dxf.default_text_content = "STYLE_TEXT"
    style.dxf.char_height = 3.5
    style.dxf.text_alignment_type = 1
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext("MY_STYLE")
    builder.set_content("note")
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))

    new_doc, new_msp = translate_entities_to_new_layout(source_msp)
    new_ml = new_msp[-1]
    new_style = new_doc.mleader_styles.get("MY_STYLE")

    assert new_style is not None
    assert new_style.dxf.default_text_content == "STYLE_TEXT"
    assert new_style.dxf.char_height == 3.5
    assert new_style.dxf.text_alignment_type == 1
    assert new_ml.dxf.style_handle == new_style.dxf.handle


def test_multileader_custom_style_arrow_to_code():
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    style = source_doc.mleader_styles.duplicate_entry("Standard", "ARROW_STYLE")
    style.set_arrow_head("DOT")
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext("ARROW_STYLE")
    builder.set_content("note")
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))

    new_doc, new_msp = translate_entities_to_new_layout(source_msp)
    new_ml = new_msp[-1]
    new_style = new_doc.mleader_styles.get("ARROW_STYLE")

    assert new_style is not None
    assert new_style.dxf.arrow_head_handle is not None
    assert new_doc.entitydb.get(new_style.dxf.arrow_head_handle).dxf.name == "_DOT"
    assert new_ml.dxf.style_handle == new_style.dxf.handle


def test_multileader_arrow_override_to_code():
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext()
    builder.set_content("note")
    builder.set_arrow_properties(name="DOT", size=2.0)
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))

    new_doc, new_msp = translate_entities_to_new_layout(source_msp)
    new_ml = new_msp[-1]

    assert new_ml.dxf.arrow_head_handle is not None
    assert new_doc.entitydb.get(new_ml.dxf.arrow_head_handle).dxf.name == "_DOT"


def test_multileader_arrow_heads_to_code():
    from ezdxf.entities.mleader import ArrowHeadData
    from ezdxf.render.arrows import ARROWS
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext()
    builder.set_content("note")
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))
    multileader = builder.multileader
    multileader.arrow_heads = [
        ArrowHeadData(0, ARROWS.arrow_handle(source_doc.blocks, "DOT")),
        ArrowHeadData(1, ARROWS.arrow_handle(source_doc.blocks, "OPEN")),
    ]

    new_doc, new_msp = translate_entities_to_new_layout(source_msp)
    new_ml = new_msp[-1]
    arrow0, arrow1 = new_ml.arrow_heads

    assert len(new_ml.arrow_heads) == 2
    assert arrow0.index == 0
    assert arrow1.index == 1
    assert new_doc.entitydb.get(arrow0.handle).dxf.name == "_DOT"
    assert new_doc.entitydb.get(arrow1.handle).dxf.name == "_OPEN"


def test_multileader_custom_style_block_reference_missing_is_safe():
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    style = source_doc.mleader_styles.duplicate_entry("Standard", "STYLE_BLOCK_STYLE")
    source_doc.blocks.new("STYLE_BLOCK")
    style.dxf.block_record_handle = source_doc.blocks.get(
        "STYLE_BLOCK"
    ).block_record_handle
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext("STYLE_BLOCK_STYLE")
    builder.set_content("note")
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))

    new_doc, new_msp = translate_entities_to_new_layout(source_msp)
    new_style = new_doc.mleader_styles.get("STYLE_BLOCK_STYLE")

    assert new_style is not None
    assert new_style.dxf.hasattr("block_record_handle") is False
    assert new_msp[-1].dxftype() == "MULTILEADER"


def test_multileader_custom_style_block_reference_preserved_if_available():
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    style = source_doc.mleader_styles.duplicate_entry("Standard", "STYLE_BLOCK_STYLE")
    source_doc.blocks.new("STYLE_BLOCK")
    style.dxf.block_record_handle = source_doc.blocks.get(
        "STYLE_BLOCK"
    ).block_record_handle
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_mtext("STYLE_BLOCK_STYLE")
    builder.set_content("note")
    builder.add_leader_line(ConnectionSide.left, [Vec2(-5, 0), Vec2(-2, 0)])
    builder.build(insert=Vec2(0, 0))

    target_doc = ezdxf.new("R2010")
    target_doc.blocks.new("STYLE_BLOCK")
    new_doc, _ = execute_entities_code_in_doc(source_msp, target_doc)
    new_style = new_doc.mleader_styles.get("STYLE_BLOCK_STYLE")

    assert new_style is not None
    assert (
        new_style.dxf.block_record_handle
        == new_doc.blocks.get("STYLE_BLOCK").block_record_handle
    )


def test_multileader_block_content_to_code():
    from ezdxf.render.mleader import ConnectionSide

    source_doc = ezdxf.new("R2010")
    block = source_doc.blocks.new("TEST_BLOCK")
    block.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=True)
    block.add_attdef("ONE", insert=(0, 0), text="ONE")
    block.add_attdef("TWO", insert=(1, 1), text="TWO")
    style = source_doc.mleader_styles.duplicate_entry("Standard", "BLOCK_STYLE")
    style.dxf.block_record_handle = block.block_record_handle
    source_msp = source_doc.modelspace()
    builder = source_msp.add_multileader_block("BLOCK_STYLE")
    builder.set_content(name="TEST_BLOCK")
    builder.set_attribute("ONE", "Data1")
    builder.set_attribute("TWO", "Data2")
    builder.add_leader_line(ConnectionSide.right, [Vec2(5, 0)])
    builder.build(insert=Vec2(0, 0))

    target_doc = ezdxf.new("R2010")
    namespace = {"ezdxf": ezdxf, "doc": target_doc, "msp": target_doc.modelspace()}
    execute_code_in_namespace(block_to_code(block, drawing="doc"), namespace)
    execute_code_in_namespace(entities_to_code(source_msp, layout="msp"), namespace)

    new_doc = namespace["doc"]
    new_msp = namespace["msp"]
    new_ml = new_msp[-1]
    new_block = new_doc.blocks.get("TEST_BLOCK")
    new_style = new_doc.mleader_styles.get("BLOCK_STYLE")
    attdef0, attdef1 = list(new_block.attdefs())
    block_attrib0, block_attrib1 = new_ml.block_attribs

    assert new_ml.dxftype() == "MULTILEADER"
    assert new_style is not None
    assert new_style.dxf.block_record_handle == new_block.block_record_handle
    assert new_ml.dxf.block_record_handle == new_block.block_record_handle
    assert new_ml.context.block is not None
    assert new_ml.context.block.block_record_handle == new_block.block_record_handle
    assert block_attrib0.handle == attdef0.dxf.handle
    assert block_attrib1.handle == attdef1.dxf.handle
    assert block_attrib0.text == "Data1"
    assert block_attrib1.text == "Data2"


def test_acad_table_text_surface_to_code():
    source_doc = ezdxf.new("R2018")
    source_msp = source_doc.modelspace()
    table = source_msp.add_table(
        (1, 2),
        [["TITLE", "STATUS"], ["HEADER", "VALUE"], ["DATA", "OK"]],
        row_heights=[11.0, 9.0, 9.0],
        col_widths=[38.0, 28.0],
    )
    table.set_row_height(0, 20.0)
    table.set_col_width(1, 30.0)
    table.set_title_suppressed(True)
    table.set_cell_text(1, 1, "VALUE-LONG")
    table.set_cell_text_height(0, 0, 20.0)
    table.set_cell_alignment(0, 1, 4)
    table.set_cell_content_color(1, 0, 215, 10507177)
    table.set_cell_fill_color(0, 1, 177, 3811732)
    table.clear_cell_fill(0, 1)

    new_doc, new_msp = translate_entities_to_new_layout(source_msp)
    new_table = next(entity for entity in new_msp if entity.dxftype() == "ACAD_TABLE")

    assert new_table.data is not None
    assert new_table.dxf.insert == table.dxf.insert
    assert new_table.data.row_heights == table.data.row_heights
    assert new_table.data.col_widths == table.data.col_widths
    assert new_table.data.suppress_title == table.data.suppress_title
    assert new_table.data.suppress_column_header == table.data.suppress_column_header
    assert [cell.text for cell in new_table.data.cells] == [cell.text for cell in table.data.cells]

    src_cells = table.data.cells
    dst_cells = new_table.data.cells
    assert dst_cells[0].text_height == src_cells[0].text_height
    assert dst_cells[1].alignment == src_cells[1].alignment
    assert dst_cells[1].fill_enabled == 1
    assert dst_cells[1].fill_color == 0
    assert dst_cells[2].text == src_cells[2].text

    assert len(list(new_table.virtual_entities())) == len(list(table.virtual_entities()))
    assert new_doc.table_styles.get("Standard") is not None


def test_acad_table_minimal_block_cell_to_code():
    source_doc = ezdxf.new("R2018")
    block = source_doc.blocks.new("TABLE_BLOCK_CELL_MIN", base_point=(0, 0))
    block.add_lwpolyline([(0, 0), (2, 0), (2, 2), (0, 2)], close=True)
    source_msp = source_doc.modelspace()
    table = source_msp.add_table((0, 0), [["T"], ["H"], [""]])
    table.set_cell_block(2, 0, "TABLE_BLOCK_CELL_MIN", block_scale=1.0, alignment=1)

    target_doc = ezdxf.new("R2018")
    namespace = {"ezdxf": ezdxf, "doc": target_doc, "msp": target_doc.modelspace()}
    execute_code_in_namespace(block_to_code(block, drawing="doc"), namespace)
    execute_code_in_namespace(entities_to_code(source_msp, layout="msp"), namespace)

    new_doc = namespace["doc"]
    new_msp = namespace["msp"]
    new_table = next(entity for entity in new_msp if entity.dxftype() == "ACAD_TABLE")
    new_cell = new_table.get_cell(2, 0)

    assert new_cell.is_block_cell is True
    assert new_cell.block_scale == 1.0
    assert new_cell.alignment == 1
    assert new_table.get_cell_block_name(2, 0) == "TABLE_BLOCK_CELL_MIN"
    inserts = [entity for entity in new_table.virtual_entities() if entity.dxftype() == "INSERT"]
    assert len(inserts) == 1
    assert inserts[0].dxf.name == "TABLE_BLOCK_CELL_MIN"


if __name__ == "__main__":
    pytest.main([__file__])
