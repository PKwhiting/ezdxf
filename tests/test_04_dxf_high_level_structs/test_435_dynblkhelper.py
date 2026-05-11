from io import StringIO

import ezdxf

from ezdxf.dynblkhelper import (
    DynamicBlockVisibilityParameter,
    DynamicBlockVisibilityState,
    get_dynamic_block_definition,
    get_dynamic_block_reference,
    get_dynamic_block_visibility_entities,
    get_dynamic_block_visibility_parameter,
    get_dynamic_block_visibility_state,
    get_dynamic_block_visibility_state_handles,
    get_dynamic_block_visibility_states,
    set_dynamic_block_reference,
    set_dynamic_block_visibility_parameter,
    set_dynamic_block_visibility_state,
)


def make_dynamic_insert(doc, current_state: str):
    msp = doc.modelspace()
    base = doc.blocks.get("DYN_VIS_PROBE_BASE")
    if base is None:
        base = doc.blocks.new("DYN_VIS_PROBE_BASE")
        parameter = DynamicBlockVisibilityParameter(
            handle="",
            label="Visibility State",
            parameter_name="Visibility1Param",
            location=(0.0, 14.0, 0.0),
            states=(
                DynamicBlockVisibilityState("STATE_A", ("EF", "EE", "ED", "EC", "F0")),
                DynamicBlockVisibilityState("STATE_B", ("F1", "F2", "EC", "ED", "EE")),
                DynamicBlockVisibilityState("STATE_C", ("F4", "F3", "F6", "F5", "EC", "EE", "ED")),
            ),
        )
        set_dynamic_block_visibility_parameter(base, parameter, guid="{GUID}")

    anon = doc.blocks.new_anonymous_block(type_char="U")
    insert = msp.add_blockref(anon.name, (0, 0))
    set_dynamic_block_reference(anon, base)
    set_dynamic_block_visibility_state(insert, base, state=current_state)
    return insert


def make_dynamic_insert_with_entities(doc, current_state: str):
    msp = doc.modelspace()
    base = doc.blocks.get("DYN_VIS_PROBE_BASE_ENTS")
    if base is None:
        base = doc.blocks.new("DYN_VIS_PROBE_BASE_ENTS")
        common1 = base.add_line((0, 0), (1, 0))
        common2 = base.add_line((0, 1), (1, 1))
        state_a = base.add_circle((1, 1), radius=0.5)
        state_b = base.add_lwpolyline([(0, 0), (1, 0), (0.5, 1)], close=True)
        state_c1 = base.add_line((0, 0), (1, 1))
        state_c2 = base.add_line((0, 1), (1, 0))
        base_handles = {
            "common1": common1.dxf.handle,
            "common2": common2.dxf.handle,
            "state_a": state_a.dxf.handle,
            "state_b": state_b.dxf.handle,
            "state_c1": state_c1.dxf.handle,
            "state_c2": state_c2.dxf.handle,
        }
        parameter = DynamicBlockVisibilityParameter(
            handle="",
            label="Visibility State",
            parameter_name="Visibility1Param",
            location=(0.0, 14.0, 0.0),
            states=(
                DynamicBlockVisibilityState(
                    "STATE_A",
                    (
                        base_handles["common1"],
                        base_handles["common2"],
                        base_handles["state_a"],
                    ),
                ),
                DynamicBlockVisibilityState(
                    "STATE_B",
                    (
                        base_handles["common1"],
                        base_handles["common2"],
                        base_handles["state_b"],
                    ),
                ),
                DynamicBlockVisibilityState(
                    "STATE_C",
                    (
                        base_handles["common1"],
                        base_handles["common2"],
                        base_handles["state_c1"],
                        base_handles["state_c2"],
                    ),
                ),
            ),
        )
        set_dynamic_block_visibility_parameter(
            base, parameter, guid="{GUID}", true_name="DYN_VIS_PROBE_BASE_ENTS"
        )
        setattr(base, "_dyn_base_handles", base_handles)
    else:
        base_handles = getattr(base, "_dyn_base_handles")

    anon = doc.blocks.new_anonymous_block(type_char="U")
    anon.add_line((0, 0), (1, 0))
    anon.add_line((0, 1), (1, 1))
    anon.add_circle((1, 1), radius=0.5)
    anon.add_lwpolyline([(0, 0), (1, 0), (0.5, 1)], close=True)
    anon.add_line((0, 0), (1, 1))
    anon.add_line((0, 1), (1, 0))
    insert = msp.add_blockref(anon.name, (0, 0))
    set_dynamic_block_reference(anon, base)
    set_dynamic_block_visibility_state(insert, base, state=current_state)
    return insert


def test_get_dynamic_block_visibility_parameter_and_state():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_insert(doc, "STATE_C")

    block = get_dynamic_block_definition(insert)
    parameter = get_dynamic_block_visibility_parameter(insert)

    assert block is not None
    assert block.name == "DYN_VIS_PROBE_BASE"
    assert parameter is not None
    assert parameter.label == "Visibility State"
    assert parameter.parameter_name == "Visibility1Param"
    assert parameter.location == (0.0, 14.0, 0.0)
    assert parameter.all_entity_handles == (
        "EF",
        "EE",
        "ED",
        "EC",
        "F0",
        "F1",
        "F2",
        "F4",
        "F3",
        "F6",
        "F5",
    )
    assert tuple(state.name for state in parameter.states) == (
        "STATE_A",
        "STATE_B",
        "STATE_C",
    )
    assert parameter.states[0].entity_handles == ("EF", "EE", "ED", "EC", "F0")
    assert parameter.states[2].entity_handles == (
        "F4",
        "F3",
        "F6",
        "F5",
        "EC",
        "EE",
        "ED",
    )
    assert get_dynamic_block_visibility_states(insert) == (
        "STATE_A",
        "STATE_B",
        "STATE_C",
    )
    assert get_dynamic_block_visibility_state(insert) == "STATE_C"


def test_get_dynamic_block_visibility_state_varies_per_insert():
    doc = ezdxf.new("R2018")
    insert_a = make_dynamic_insert(doc, "STATE_A")
    insert_b = make_dynamic_insert(doc, "STATE_B")

    assert get_dynamic_block_visibility_state(insert_a) == "STATE_A"
    assert get_dynamic_block_visibility_state(insert_b) == "STATE_B"


def test_get_dynamic_block_visibility_entities_resolves_base_and_reference_entities():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_insert_with_entities(doc, "STATE_C")

    base = get_dynamic_block_definition(insert)
    ref = get_dynamic_block_reference(insert)

    assert base is not None
    assert ref is not None
    assert get_dynamic_block_visibility_state_handles(insert) == tuple(
        entity.dxf.handle for entity in get_dynamic_block_visibility_entities(base, "STATE_C")
    )

    base_entities = get_dynamic_block_visibility_entities(base, "STATE_C")
    ref_entities = get_dynamic_block_visibility_entities(insert)

    assert [entity.dxftype() for entity in base_entities] == [
        "LINE",
        "LINE",
        "LINE",
        "LINE",
    ]
    assert [entity.dxftype() for entity in ref_entities] == [
        "LINE",
        "LINE",
        "LINE",
        "LINE",
    ]
    assert tuple(entity.dxf.handle for entity in ref_entities) == tuple(
        entity.dxf.handle for entity in list(ref)[:2] + list(ref)[4:6]
    )


def test_dynamic_block_visibility_roundtrip_preserves_visibility_helpers():
    doc = ezdxf.new("R2018")
    make_dynamic_insert_with_entities(doc, "STATE_A")
    make_dynamic_insert_with_entities(doc, "STATE_C")

    stream = StringIO()
    doc.write(stream)
    loaded = ezdxf.read(StringIO(stream.getvalue()))
    inserts = list(loaded.modelspace().query("INSERT"))

    assert get_dynamic_block_visibility_state(inserts[0]) == "STATE_A"
    assert get_dynamic_block_visibility_state(inserts[1]) == "STATE_C"
    assert get_dynamic_block_visibility_states(inserts[0]) == (
        "STATE_A",
        "STATE_B",
        "STATE_C",
    )
    assert [entity.dxftype() for entity in get_dynamic_block_visibility_entities(inserts[1])] == [
        "LINE",
        "LINE",
        "LINE",
        "LINE",
    ]


def test_dynamic_block_helpers_register_required_appids():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_insert(doc, "STATE_A")

    assert insert is not None
    for name in (
        "AcDbDynamicBlockGUID",
        "AcDbDynamicBlockTrueName",
        "AcDbBlockRepETag",
        "AcDbBlockRepBTag",
    ):
        assert name in doc.appids


def test_dynamic_block_reference_gets_xdict_and_blkrefs_appdata():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_insert(doc, "STATE_A")
    reference = get_dynamic_block_reference(insert)

    assert reference is not None
    assert reference.block_record.has_extension_dict is True
    assert reference.block_record.blkref_handles == [insert.dxf.handle]


def test_dynamic_block_visibility_writing_adds_required_classes():
    doc = ezdxf.new("R2018")
    make_dynamic_insert(doc, "STATE_A")

    stream = StringIO()
    doc.write(stream)
    data = stream.getvalue()

    assert "AcDbEvalGraph" in data
    assert "AcAeEditorObj" in data
    assert "AcAeEEMgrObj" in data
    assert "AcDbBlockVisibilityParameter" in data
    assert "AcDbBlockVisibilityGrip" in data
    assert "AcDbBlockRepresentationData" in data

    loaded = ezdxf.read(StringIO(data))
    counts = {
        cls.dxf.name: cls.dxf.get("instance_count")
        for cls in loaded.classes
        if cls.dxf.name
        in {
            "ACAD_EVALUATION_GRAPH",
            "BLOCKVISIBILITYPARAMETER",
            "BLOCKVISIBILITYGRIP",
            "BLOCKGRIPLOCATIONCOMPONENT",
            "ACDB_DYNAMICBLOCKPURGEPREVENTER_VERSION",
            "ACDB_BLOCKREPRESENTATION_DATA",
        }
    }
    assert counts["ACAD_EVALUATION_GRAPH"] == 1
    assert counts["BLOCKVISIBILITYPARAMETER"] == 1
    assert counts["BLOCKVISIBILITYGRIP"] == 1
    assert counts["BLOCKGRIPLOCATIONCOMPONENT"] == 2


def test_dynamic_block_entities_get_block_rep_etag_xdata():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_insert_with_entities(doc, "STATE_B")
    base = get_dynamic_block_definition(insert)
    ref = get_dynamic_block_reference(insert)

    assert base is not None
    assert ref is not None
    for index, entity in enumerate(base):
        tags = entity.get_xdata("AcDbBlockRepETag")
        assert list(tags) == [(1070, 1), (1071, index), (1005, entity.dxf.handle)]
    for index, entity in enumerate(ref):
        tags = entity.get_xdata("AcDbBlockRepETag")
        assert list(tags) == [(1070, 1), (1071, index), (1005, entity.dxf.handle)]


def test_dynamic_block_insert_enhanced_cache_sets_reactors():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_insert(doc, "STATE_A")

    rep = insert.get_extension_dict().dictionary.get("AcDbBlockRepresentation")
    cache = rep.get("AppDataCache")
    enhanced = cache.get("ACAD_ENHANCEDBLOCKDATA")
    xrecord = enhanced.get("6")

    assert enhanced.get_reactors() == [cache.dxf.handle]
    assert xrecord.get_reactors() == [enhanced.dxf.handle]


def test_dynamic_block_writer_applies_invisible_mask_to_default_and_active_states():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_insert_with_entities(doc, "STATE_C")

    base = doc.blocks.get("DYN_VIS_PROBE_BASE_ENTS")
    ref = get_dynamic_block_reference(insert)

    assert base is not None
    assert ref is not None

    # Base dynamic definition defaults to the first state (STATE_A).
    base_invisible = [entity.dxf.get("invisible", 0) for entity in base]
    assert base_invisible == [0, 0, 0, 1, 1, 1]

    # Active anonymous reference reflects the requested current state (STATE_C).
    ref_invisible = [entity.dxf.get("invisible", 0) for entity in ref]
    assert ref_invisible == [0, 0, 1, 1, 0, 0]
