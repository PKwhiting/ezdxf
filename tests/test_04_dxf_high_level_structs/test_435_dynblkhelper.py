from io import StringIO

import pytest
import ezdxf
from ezdxf.dynblkhelper import (
    _new_tag_storage_object,
    DynamicBlockPropertiesTable,
    DynamicBlockPropertyColumn,
    DynamicBlockPropertyRow,
    DynamicBlockLinearGrip,
    DynamicBlockLinearParameter,
    DynamicBlockStretchAction,
    DynamicBlockStretchActionTarget,
    DynamicBlockVisibilityParameter,
    DynamicBlockVisibilityState,
    get_dynamic_block_definition,
    get_dynamic_block_linear_grips,
    get_dynamic_block_linear_parameters,
    get_dynamic_block_properties_table,
    get_dynamic_block_property_columns,
    get_dynamic_block_property_assoc_networks,
    get_dynamic_block_property_representation_families,
    get_dynamic_block_property_representations,
    get_dynamic_block_property_rows,
    set_dynamic_block_properties_editor_support,
    get_dynamic_block_reference,
    get_dynamic_block_stretch_actions,
    get_dynamic_block_visibility_entities,
    get_dynamic_block_visibility_parameter,
    get_dynamic_block_visibility_state,
    get_dynamic_block_visibility_state_handles,
    get_dynamic_block_visibility_states,
    set_dynamic_block_linear_parameter,
    set_dynamic_block_properties_table,
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


def make_dynamic_properties_insert(doc):
    msp = doc.modelspace()
    base = doc.blocks.new("DYN_PROP_PROBE_BASE")
    base.add_line((0, 0), (1, 0))
    base.add_line((0, 1), (1, 1))
    base.add_circle((1, 1), radius=0.5)
    attdef1 = base.add_attdef("PARAM_1", insert=(10, 14), text="Block Table1")
    attdef2 = base.add_attdef("PARAM_2", insert=(10, 10), text="Block Table1")
    attdef3 = base.add_attdef("PARAM_3", insert=(10, 6), text="Block Table1")

    parameter = DynamicBlockVisibilityParameter(
        handle="",
        label="Visibility State",
        parameter_name="Visibility1Param",
        location=(0.0, 14.0, 0.0),
        states=(
            DynamicBlockVisibilityState("STATE_A", tuple(e.dxf.handle for e in base if e.dxftype() != "ATTDEF")),
            DynamicBlockVisibilityState("STATE_B", tuple(e.dxf.handle for e in base if e.dxftype() != "ATTDEF")),
            DynamicBlockVisibilityState("STATE_C", tuple(e.dxf.handle for e in base if e.dxftype() != "ATTDEF")),
        ),
    )
    set_dynamic_block_visibility_parameter(base, parameter, guid="{GUID}", true_name="DYN_PROP_PROBE_BASE")
    table = DynamicBlockPropertiesTable(
        handle="",
        label="Block Table",
        table_name="Block Table1",
        description="",
        location=(32.0, 20.0, 0.0),
        grip_location=(32.0, 20.0, 0.0),
        columns=(
            DynamicBlockPropertyColumn(attdef1.dxf.handle, "ATTDEF", "PARAM_1", "Block Table1"),
            DynamicBlockPropertyColumn(attdef2.dxf.handle, "ATTDEF", "PARAM_2", "Block Table1"),
            DynamicBlockPropertyColumn(attdef3.dxf.handle, "ATTDEF", "PARAM_3", "Block Table1"),
            DynamicBlockPropertyColumn("", "BLOCKVISIBILITYPARAMETER", "VisibilityState", "VisibilityState"),
        ),
        rows=(
            DynamicBlockPropertyRow(0, ("VAL 1", "VAL 1", "VAL 1", "STATE_A")),
            DynamicBlockPropertyRow(1, ("VAL 2", "VAL 1", "VAL 3", "STATE_B")),
            DynamicBlockPropertyRow(2, ("VAL 3", "VAL 2", "VAL 1", "STATE_C")),
        ),
    )
    set_dynamic_block_properties_table(base, table)
    set_dynamic_block_properties_editor_support(base, table)

    anon = doc.blocks.new_anonymous_block(type_char="U")
    anon.add_line((0, 0), (1, 0))
    anon.add_line((0, 1), (1, 1))
    anon.add_circle((1, 1), radius=0.5)
    set_dynamic_block_reference(anon, base)
    insert = msp.add_blockref(anon.name, (0, 0))
    set_dynamic_block_visibility_state(insert, base, state="STATE_A")
    return insert


def attach_linear_stretch_probe(block):
    doc = block.doc
    assert doc is not None
    graph = block.block_record.get_extension_dict().dictionary.get("ACAD_ENHANCEDBLOCK")
    assert graph is not None

    table = get_dynamic_block_properties_table(block)
    assert table is not None

    grip = next(obj for obj in doc.objects if obj.dxftype() == "BLOCKPROPERTIESTABLEGRIP")
    entities = list(block)
    stretch_entity = entities[0]
    attdef1 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_1")
    attdef2 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_2")
    attdef3 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_3")

    linear = _new_tag_storage_object(
        doc,
        "BLOCKLINEARPARAMETER",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 45), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, "Linear"), (98, 33), (99, 378), (1071, 32)],
            [(100, "AcDbBlockParameter"), (280, 1), (281, 0)],
            [
                (100, "AcDbBlock2PtParameter"),
                (1010, (0.0, 0.0, 0.0)),
                (1011, (1.0, 0.0, 0.0)),
                (170, 4),
                (91, 49),
                (91, 46),
                (91, 0),
                (91, 0),
                (171, 1),
                (92, 49),
                (301, "DisplacementX"),
                (172, 1),
                (93, 49),
                (302, "DisplacementY"),
                (173, 1),
                (94, 46),
                (303, "DisplacementX"),
                (174, 1),
                (95, 46),
                (304, "DisplacementY"),
                (177, 0),
            ],
            [
                (100, "AcDbBlockLinearParameter"),
                (305, "Distance1"),
                (306, ""),
                (140, 1.0),
                (307, ""),
                (96, 1),
                (141, 0.0),
                (142, 0.0),
                (143, 0.0),
                (175, 0),
            ],
        ],
    )
    end_grip = _new_tag_storage_object(
        doc,
        "BLOCKLINEARGRIP",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 46), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, "End Grip"), (98, 33), (99, 378), (1071, 0)],
            [(100, "AcDbBlockGrip"), (91, 47), (92, 48), (1010, (1.0, 0.0, 0.0)), (280, 1), (93, -1)],
            [(100, "AcDbBlockLinearGrip"), (140, 1.0), (141, 0.0), (142, 0.0)],
        ],
    )
    _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 47), (98, 33), (99, 378), (1, ""), (70, 40), (140, 1.797693134862314e+99)],
            [(100, "AcDbBlockGripExpr"), (91, 45), (300, "UpdatedEndX")],
        ],
    )
    _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 48), (98, 33), (99, 378), (1, ""), (70, 40), (140, 1.797693134862314e+99)],
            [(100, "AcDbBlockGripExpr"), (91, 45), (300, "UpdatedEndY")],
        ],
    )
    base_grip = _new_tag_storage_object(
        doc,
        "BLOCKLINEARGRIP",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 49), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, "Base Grip"), (98, 33), (99, 378), (1071, 0)],
            [(100, "AcDbBlockGrip"), (91, 50), (92, 51), (1010, (0.0, 0.0, 0.0)), (280, 1), (93, -1)],
            [(100, "AcDbBlockLinearGrip"), (140, -1.0), (141, 0.0), (142, 0.0)],
        ],
    )
    _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 50), (98, 33), (99, 378), (1, ""), (70, 40), (140, 0.0)],
            [(100, "AcDbBlockGripExpr"), (91, 45), (300, "UpdatedBaseX")],
        ],
    )
    _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 51), (98, 33), (99, 378), (1, ""), (70, 40), (140, 0.0)],
            [(100, "AcDbBlockGripExpr"), (91, 45), (300, "UpdatedBaseY")],
        ],
    )
    stretch = _new_tag_storage_object(
        doc,
        "BLOCKSTRETCHACTION",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 52), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, "Stretch1"), (98, 33), (99, 378), (1071, 0)],
            [
                (100, "AcDbBlockAction"),
                (70, 1),
                (91, 32),
                (71, 6),
                (330, grip.dxf.handle),
                (330, table.handle),
                (330, attdef3.dxf.handle),
                (330, attdef2.dxf.handle),
                (330, attdef1.dxf.handle),
                (330, stretch_entity.dxf.handle),
                (1010, (1.0, -0.5, 0.0)),
            ],
            [
                (100, "AcDbBlockStretchAction"),
                (92, 45),
                (301, "EndXDelta"),
                (93, 45),
                (302, "EndYDelta"),
                (72, 2),
                (1011, (2.0, 1.0, 0.0)),
                (1011, (0.5, -0.5, 0.0)),
                (73, 4),
                (331, stretch_entity.dxf.handle),
                (74, 2),
                (94, 1),
                (94, 2),
                (331, attdef1.dxf.handle),
                (74, 1),
                (94, 0),
                (331, attdef2.dxf.handle),
                (74, 1),
                (94, 0),
                (331, attdef3.dxf.handle),
                (74, 1),
                (94, 0),
                (75, 1),
                (95, 32),
                (76, 1),
                (94, 0),
                (140, 1.0),
                (141, 0.0),
                (280, 0),
            ],
        ],
    )

    return linear, end_grip, base_grip, stretch


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


def test_dynamic_block_properties_writer_adds_visibility_only_support_blocks():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)

    assert insert is not None
    zero_carrier_blocks = []
    for block in doc.blocks:
        if not block.name.startswith("*U"):
            continue
        if not any(entity.dxftype() == "ATTDEF" for entity in block):
            zero_carrier_blocks.append(block)
    assert len(zero_carrier_blocks) == 5


def test_get_dynamic_block_properties_table_reads_columns_rows_and_grip_location():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)

    table = get_dynamic_block_properties_table(insert)

    assert isinstance(table, DynamicBlockPropertiesTable)
    assert table.label == "Block Table"
    assert table.table_name == "Block Table1"
    assert table.location == (32.0, 20.0, 0.0)
    assert table.grip_location == (32.0, 20.0, 0.0)
    assert table.description == ""
    assert [column.source_dxftype for column in table.columns] == [
        "ATTDEF",
        "ATTDEF",
        "ATTDEF",
        "BLOCKVISIBILITYPARAMETER",
    ]
    assert [column.name for column in table.columns] == [
        "PARAM_1",
        "PARAM_2",
        "PARAM_3",
        "VisibilityState",
    ]
    assert [row.values for row in table.rows] == [
        ("VAL 1", "VAL 1", "VAL 1", "STATE_A"),
        ("VAL 2", "VAL 1", "VAL 3", "STATE_B"),
        ("VAL 3", "VAL 2", "VAL 1", "STATE_C"),
    ]


def test_dynamic_block_property_column_and_row_helpers():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)

    columns = get_dynamic_block_property_columns(insert)
    rows = get_dynamic_block_property_rows(insert)

    assert len(columns) == 4
    assert isinstance(columns[0], DynamicBlockPropertyColumn)
    assert len(rows) == 3
    assert isinstance(rows[0], DynamicBlockPropertyRow)
    assert rows[1].index == 1


def test_dynamic_block_properties_writer_adds_attdef_support_metadata():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = doc.blocks.get("DYN_PROP_PROBE_BASE")

    assert insert is not None
    assert base is not None

    attdefs = [entity for entity in base if entity.dxftype() == "ATTDEF"]
    assert len(attdefs) == 3
    for attdef in attdefs:
        assert attdef.has_extension_dict is True
        assert "AcadAnnotative" in attdef.xdata.data
        context_root = attdef.get_extension_dict().dictionary.get("AcDbContextDataManager")
        assert context_root is not None


def test_dynamic_block_properties_writer_clones_attdefs_into_active_reference():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    table = get_dynamic_block_properties_table(insert)
    ref = get_dynamic_block_reference(insert)

    assert table is not None
    assert ref is not None
    attdefs = [entity for entity in ref if entity.dxftype() == "ATTDEF"]
    assert [attdef.dxf.tag for attdef in attdefs] == ["PARAM_1", "PARAM_2", "PARAM_3"]
    assert [attdef.dxf.get("invisible", 0) for attdef in attdefs] == [0, 0, 0]
    assert [attdef.get_reactors() for attdef in attdefs] == [[table.handle], [table.handle], [table.handle]]


def test_dynamic_block_properties_writer_marks_property_graph_links():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = get_dynamic_block_definition(insert)
    table = get_dynamic_block_properties_table(insert)

    assert base is not None
    assert table is not None
    assert base.block_record.has_xdata("AcDbDynamicBlockTrueName2") is True
    assert base.block_record.has_xdata("AcDbDynamicBlockTrueName") is False

    graph = next(obj for obj in doc.objects if obj.dxftype() == "ACAD_EVALUATION_GRAPH")
    visibility = next(obj for obj in doc.objects if obj.dxftype() == "BLOCKVISIBILITYPARAMETER")

    assert graph.has_xdata("AcadBPTGraphNodeId") is True
    assert visibility.get_reactors() == [table.handle]


def test_dynamic_block_properties_writer_hides_attdefs_for_nondefault_state():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = doc.blocks.get("DYN_PROP_PROBE_BASE")
    ref = get_dynamic_block_reference(insert)

    assert base is not None
    assert ref is not None
    set_dynamic_block_visibility_state(insert, base, state="STATE_B")

    attdefs = [entity for entity in ref if entity.dxftype() == "ATTDEF"]
    assert [attdef.dxf.get("invisible", 0) for attdef in attdefs] == [1, 1, 1]


def test_dynamic_block_properties_writer_root_assocnetwork_is_direct():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)

    assert insert is not None
    root = doc.rootdict.get("ACAD_ASSOCNETWORK")
    assert root is not None
    assert root.dxftype() == "DICTIONARY"
    assoc = root.get("ACAD_ASSOCNETWORK")
    assert assoc is not None
    assert assoc.dxftype() == "ACDBASSOCNETWORK"


def test_dynamic_block_properties_writer_sets_table_reactors_on_hidden_carriers():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    table = get_dynamic_block_properties_table(insert)
    reps = [rep for rep in get_dynamic_block_property_representations(insert) if not rep.is_active]

    assert table is not None
    assert reps
    hidden_block = doc.blocks.get(reps[0].block_name)
    assert hidden_block is not None
    for attdef in hidden_block:
        if attdef.dxftype() == "ATTDEF":
            assert attdef.get_reactors() == [table.handle]


def test_dynamic_block_property_assoc_networks_are_empty_for_minimal_authored_fixture():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)

    networks = get_dynamic_block_property_assoc_networks(insert)

    assert len(networks) == 3
    assert [(var.name, var.value) for var in networks[0].variables] == [
        ("user1", "1"),
        ("user2", "1"),
    ]


def test_dynamic_block_property_representations_include_active_blocks():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)

    reps = get_dynamic_block_property_representations(insert)

    assert len(reps) == 7
    rep = next(r for r in reps if r.is_active)
    assert rep.is_active is True
    assert rep.block_name.startswith("*U")
    assert [carrier.tag for carrier in rep.carriers] == ["PARAM_1", "PARAM_2", "PARAM_3"]
    assert [carrier.invisible for carrier in rep.carriers] == [0, 0, 0]


def test_dynamic_block_property_representation_families_group_by_signature():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)

    families = get_dynamic_block_property_representation_families(insert)

    assert len(families) == 5
    counts = {
        (
            family.carrier_count,
            family.carrier_texts,
            family.carrier_visibility,
            family.assoc_signature,
        ): len(family.block_names)
        for family in families
    }
    assert counts[(2, ("", ""), (0, 0), (("user1", "1"), ("user2", "1")))] == 1
    assert counts[(2, ("", ""), (1, 1), (("user1", "2"), ("user2", "1")))] == 1
    assert counts[(2, ("", ""), (1, 1), (("user1", "3"), ("user2", "2")))] == 1
    assert counts[(3, ("Block Table1", "Block Table1", "Block Table1"), (0, 0, 0), ())] == 2
    assert counts[(3, ("Block Table1", "Block Table1", "Block Table1"), (1, 1, 1), ())] == 2


def test_dynamic_block_properties_editor_support_rerun_replaces_hidden_support():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = get_dynamic_block_definition(insert)
    table = get_dynamic_block_properties_table(base)

    assert base is not None
    assert table is not None
    reps_before = get_dynamic_block_property_representations(base)
    assoc_before = get_dynamic_block_property_assoc_networks(base)
    anon_before = sum(1 for block in doc.blocks if block.name.startswith("*U"))

    set_dynamic_block_properties_editor_support(base, table)

    reps_after = get_dynamic_block_property_representations(base)
    assoc_after = get_dynamic_block_property_assoc_networks(base)
    anon_after = sum(1 for block in doc.blocks if block.name.startswith("*U"))

    assert len(reps_after) == len(reps_before)
    assert len(assoc_after) == len(assoc_before)
    assert anon_after == anon_before


def test_get_dynamic_block_linear_parameters_and_grips_reads_linear_stack():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = get_dynamic_block_definition(insert)

    assert base is not None
    linear_entity, end_grip_entity, base_grip_entity, _ = attach_linear_stretch_probe(base)

    parameters = get_dynamic_block_linear_parameters(insert)
    grips = get_dynamic_block_linear_grips(base)

    assert len(parameters) == 1
    assert isinstance(parameters[0], DynamicBlockLinearParameter)
    assert parameters[0].handle == linear_entity.dxf.handle
    assert parameters[0].label == "Linear"
    assert parameters[0].parameter_name == "Distance1"
    assert parameters[0].base_point == (0.0, 0.0, 0.0)
    assert parameters[0].end_point == (1.0, 0.0, 0.0)
    assert parameters[0].distance == 1.0
    assert parameters[0].base_grip_handle == base_grip_entity.dxf.handle
    assert parameters[0].end_grip_handle == end_grip_entity.dxf.handle
    assert parameters[0].base_grip_label == "Base Grip"
    assert parameters[0].end_grip_label == "End Grip"

    assert len(grips) == 2
    assert all(isinstance(grip, DynamicBlockLinearGrip) for grip in grips)
    grip_by_label = {grip.label: grip for grip in grips}
    assert grip_by_label["Base Grip"].offset == (-1.0, 0.0, 0.0)
    assert grip_by_label["End Grip"].offset == (1.0, 0.0, 0.0)
    assert grip_by_label["End Grip"].location == (1.0, 0.0, 0.0)


def test_get_dynamic_block_stretch_actions_reads_targets_and_selection_window():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = get_dynamic_block_definition(insert)

    assert base is not None
    _, _, _, stretch_entity = attach_linear_stretch_probe(base)

    actions = get_dynamic_block_stretch_actions(insert)

    assert len(actions) == 1
    assert isinstance(actions[0], DynamicBlockStretchAction)
    assert actions[0].handle == stretch_entity.dxf.handle
    assert actions[0].label == "Stretch1"
    assert actions[0].action_location == (1.0, -0.5, 0.0)
    assert actions[0].x_expr_id == 45
    assert actions[0].x_name == "EndXDelta"
    assert actions[0].y_expr_id == 45
    assert actions[0].y_name == "EndYDelta"
    assert actions[0].selection_window == ((2.0, 1.0, 0.0), (0.5, -0.5, 0.0))
    assert len(actions[0].dependency_handles) == 6
    assert [target.mode for target in actions[0].targets] == [2, 1, 1, 1]
    assert actions[0].targets[0].components == (1, 2)
    assert actions[0].targets[1].components == (0,)


def test_set_dynamic_block_linear_parameter_patches_graph_and_visibility():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = get_dynamic_block_definition(insert)

    assert base is not None
    entities = list(base)
    stretch_entity = entities[0]
    attdef1 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_1")
    attdef2 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_2")
    attdef3 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_3")
    table = get_dynamic_block_properties_table(base)
    grip = next(obj for obj in doc.objects if obj.dxftype() == "BLOCKPROPERTIESTABLEGRIP")

    assert table is not None
    parameter = DynamicBlockLinearParameter(
        handle="",
        label="Linear",
        parameter_name="Distance1",
        description="",
        base_point=(0.0, 0.0, 0.0),
        end_point=(1.0, 0.0, 0.0),
        distance=1.0,
        expr_id=0,
        base_grip_label="Base Grip",
        end_grip_label="End Grip",
    )
    action = DynamicBlockStretchAction(
        handle="",
        label="Stretch1",
        action_location=(1.0, -0.5, 0.0),
        x_expr_id=0,
        x_name="EndXDelta",
        y_expr_id=0,
        y_name="EndYDelta",
        selection_window=((2.0, 1.0, 0.0), (0.5, -0.5, 0.0)),
        dependency_handles=(
            grip.dxf.handle,
            table.handle,
            attdef3.dxf.handle,
            attdef2.dxf.handle,
            attdef1.dxf.handle,
            stretch_entity.dxf.handle,
        ),
        targets=(
            DynamicBlockStretchActionTarget(stretch_entity.dxf.handle, 2, (1, 2)),
            DynamicBlockStretchActionTarget(attdef1.dxf.handle, 1, (0,)),
            DynamicBlockStretchActionTarget(attdef2.dxf.handle, 1, (0,)),
            DynamicBlockStretchActionTarget(attdef3.dxf.handle, 1, (0,)),
        ),
    )

    created = set_dynamic_block_linear_parameter(base, parameter, action)
    linear = get_dynamic_block_linear_parameters(base)
    actions = get_dynamic_block_stretch_actions(base)
    grips = get_dynamic_block_linear_grips(base)
    visibility = get_dynamic_block_visibility_parameter(base)

    assert created.handle
    assert len(linear) == 1
    assert linear[0].handle == created.handle
    assert linear[0].base_grip_label == "Base Grip"
    assert linear[0].end_grip_label == "End Grip"
    assert len(actions) == 1
    assert actions[0].label == "Stretch1"
    assert len(grips) == 2
    assert visibility is not None
    assert tuple(len(state.entity_handles) for state in visibility.states) == (6, 6, 6)
    assert len(visibility.all_entity_handles) == 6

    set_dynamic_block_visibility_state(insert, base, state="STATE_B")
    ref = get_dynamic_block_reference(insert)

    assert ref is not None
    assert [entity.dxf.get("invisible", 0) for entity in ref if entity.dxftype() == "ATTDEF"] == [0, 0, 0]


def test_set_dynamic_block_properties_table_preserves_existing_linear_parameter():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = get_dynamic_block_definition(insert)

    assert base is not None
    entities = list(base)
    stretch_entity = entities[0]
    attdef1 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_1")
    attdef2 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_2")
    attdef3 = next(entity for entity in entities if entity.dxftype() == "ATTDEF" and entity.dxf.tag == "PARAM_3")
    table = get_dynamic_block_properties_table(base)
    grip = next(obj for obj in doc.objects if obj.dxftype() == "BLOCKPROPERTIESTABLEGRIP")

    assert table is not None
    linear = DynamicBlockLinearParameter(
        handle="",
        label="Linear",
        parameter_name="Distance1",
        description="",
        base_point=(0.0, 0.0, 0.0),
        end_point=(1.0, 0.0, 0.0),
        distance=1.0,
        expr_id=0,
        base_grip_label="Base Grip",
        end_grip_label="End Grip",
    )
    action = DynamicBlockStretchAction(
        handle="",
        label="Stretch1",
        action_location=(1.0, -0.5, 0.0),
        x_expr_id=0,
        x_name="EndXDelta",
        y_expr_id=0,
        y_name="EndYDelta",
        selection_window=((2.0, 1.0, 0.0), (0.5, -0.5, 0.0)),
        dependency_handles=(
            grip.dxf.handle,
            table.handle,
            attdef3.dxf.handle,
            attdef2.dxf.handle,
            attdef1.dxf.handle,
            stretch_entity.dxf.handle,
        ),
        targets=(
            DynamicBlockStretchActionTarget(stretch_entity.dxf.handle, 2, (1, 2)),
            DynamicBlockStretchActionTarget(attdef1.dxf.handle, 1, (0,)),
            DynamicBlockStretchActionTarget(attdef2.dxf.handle, 1, (0,)),
            DynamicBlockStretchActionTarget(attdef3.dxf.handle, 1, (0,)),
        ),
    )
    set_dynamic_block_linear_parameter(base, linear, action)

    rewritten = DynamicBlockPropertiesTable(
        handle="",
        label=table.label,
        table_name=table.table_name,
        description=table.description,
        location=table.location,
        grip_location=table.grip_location,
        columns=table.columns,
        rows=table.rows,
    )
    set_dynamic_block_properties_table(base, rewritten)

    new_linear = get_dynamic_block_linear_parameters(base)
    new_actions = get_dynamic_block_stretch_actions(base)

    assert len(new_linear) == 1
    assert new_linear[0].parameter_name == "Distance1"
    assert new_linear[0].base_grip_label == "Base Grip"
    assert len(new_actions) == 1
    assert new_actions[0].label == "Stretch1"


def test_set_dynamic_block_linear_parameter_rejects_second_linear_parameter():
    doc = ezdxf.new("R2018")
    insert = make_dynamic_properties_insert(doc)
    base = get_dynamic_block_definition(insert)

    assert base is not None
    parameter = DynamicBlockLinearParameter(
        handle="",
        label="Linear",
        parameter_name="Distance1",
        description="",
        base_point=(0.0, 0.0, 0.0),
        end_point=(1.0, 0.0, 0.0),
        distance=1.0,
        expr_id=0,
        base_grip_label="Base Grip",
        end_grip_label="End Grip",
    )
    action = DynamicBlockStretchAction(
        handle="",
        label="Stretch1",
        action_location=(1.0, -0.5, 0.0),
        x_expr_id=0,
        x_name="EndXDelta",
        y_expr_id=0,
        y_name="EndYDelta",
        selection_window=((2.0, 1.0, 0.0), (0.5, -0.5, 0.0)),
        dependency_handles=(),
        targets=(),
    )
    set_dynamic_block_linear_parameter(base, parameter, action)

    with pytest.raises(ezdxf.DXFValueError):
        set_dynamic_block_linear_parameter(base, parameter, action)
