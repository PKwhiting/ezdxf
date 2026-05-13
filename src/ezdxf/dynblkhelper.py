#  Copyright (c) 2023, Manfred Moitzi
#  License: MIT License
"""
This module provides helper tools to work with dynamic blocks.

The current state supports only reading information from dynamic blocks, it does not
support the creation of new dynamic blocks nor the modification of them.

"""
from __future__ import annotations
from dataclasses import dataclass
import uuid
from typing import TYPE_CHECKING, Any, Iterator, Optional, Sequence, Union
from ezdxf.entities import Insert, DXFTagStorage, XRecord, Dictionary
from ezdxf.lldxf import const

if TYPE_CHECKING:
    from ezdxf.document import Drawing
    from ezdxf.layouts import BlockLayout
    from ezdxf.entities import BlockRecord, DXFEntity

__all__ = [
    "DynamicBlockVisibilityState",
    "DynamicBlockVisibilityParameter",
    "DynamicBlockLinearGrip",
    "DynamicBlockLinearParameter",
    "DynamicBlockStretchActionTarget",
    "DynamicBlockStretchAction",
    "DynamicBlockPropertyColumn",
    "DynamicBlockPropertyRow",
    "DynamicBlockPropertiesTable",
    "DynamicBlockAssocVariable",
    "DynamicBlockAssocNetwork",
    "DynamicBlockPropertyCarrier",
    "DynamicBlockPropertyRepresentation",
    "get_dynamic_block_definition",
    "get_dynamic_block_reference",
    "is_dynamic_block_definition",
    "get_dynamic_block_record_handle",
    "get_dynamic_block_visibility_parameter",
    "get_dynamic_block_visibility_states",
    "get_dynamic_block_visibility_state",
    "get_dynamic_block_visibility_state_handles",
    "get_dynamic_block_visibility_entities",
    "get_dynamic_block_linear_grips",
    "get_dynamic_block_linear_parameters",
    "get_dynamic_block_stretch_actions",
    "get_dynamic_block_properties_table",
    "get_dynamic_block_property_columns",
    "get_dynamic_block_property_rows",
    "get_dynamic_block_property_assoc_networks",
    "get_dynamic_block_property_representations",
    "get_dynamic_block_property_representation_families",
    "set_dynamic_block_linear_parameter",
    "set_dynamic_block_properties_editor_support",
    "set_dynamic_block_properties_table",
    "set_dynamic_block_visibility_parameter",
    "set_dynamic_block_reference",
    "set_dynamic_block_visibility_state",
]

AcDbDynamicBlockGUID = "AcDbDynamicBlockGUID"
AcDbBlockRepBTag = "AcDbBlockRepBTag"
AcDbDynamicBlockTrueName = "AcDbDynamicBlockTrueName"
AcDbDynamicBlockTrueName2 = "AcDbDynamicBlockTrueName2"
AcDbBlockRepETag = "AcDbBlockRepETag"
AcadBPTGraphNodeId = "AcadBPTGraphNodeId"


def _ensure_dynamic_block_appids(doc: Drawing) -> None:
    for name in (
        AcDbDynamicBlockGUID,
        AcDbDynamicBlockTrueName,
        AcDbBlockRepETag,
        AcDbBlockRepBTag,
    ):
        if name not in doc.appids:
            doc.appids.new(name)


def _ensure_dynamic_block_properties_appids(doc: Drawing) -> None:
    for name in (AcDbDynamicBlockTrueName2, AcadBPTGraphNodeId):
        if name not in doc.appids:
            doc.appids.new(name)


def _tag_block_representation_entities(block: BlockLayout) -> None:
    for index, entity in enumerate(block):
        entity.set_xdata(
            AcDbBlockRepETag,
            [(1070, 1), (1071, index), (1005, entity.dxf.handle)],
        )


def _default_annotation_scale_handle(doc: Drawing) -> str:
    scale_root = doc.rootdict.get_required_dict("ACAD_SCALELIST")
    scale = scale_root.get("A0")
    if scale is None:
        scale = _new_tag_storage_object(
            doc,
            "SCALE",
            scale_root.dxf.handle,
            [[(100, "AcDbScale"), (70, 0), (300, "1:1"), (140, 1.0), (141, 1.0), (290, 1)]],
        )
        scale.set_reactors([scale_root.dxf.handle])
        scale_root.add("A0", scale)
    if scale is None:
        for _, entity in scale_root.items():
            scale = entity
            break
    if scale is None:
        raise const.DXFStructureError("ACAD_SCALELIST requires at least one SCALE entry")
    return scale.dxf.handle


def _set_property_attdef_rep_etag(attdef, rep_index: int) -> None:
    attdef.set_xdata(AcDbBlockRepETag, [(1070, 1), (1071, rep_index), (1005, "0")])


def _ensure_property_attdef_annotative_metadata(attdef) -> None:
    doc = attdef.doc
    if doc is None:
        raise const.DXFStructureError("valid DXF document required")
    if "AcadAnnotative" not in doc.appids:
        doc.appids.new("AcadAnnotative")

    attdef.set_xdata(
        "AcadAnnotative",
        [
            (1000, "AnnotativeData"),
            (1002, "{"),
            (1070, 1),
            (1070, 1),
            (1002, "}"),
        ],
    )

    xdict = attdef.get_extension_dict() if attdef.has_extension_dict else attdef.new_extension_dict()
    root = xdict.dictionary
    context_manager = root.get("AcDbContextDataManager")
    if not isinstance(context_manager, Dictionary):
        context_manager = root.add_new_dict("AcDbContextDataManager")
    annot_scales = context_manager.get("ACDB_ANNOTATIONSCALES")
    if not isinstance(annot_scales, Dictionary):
        annot_scales = context_manager.add_new_dict("ACDB_ANNOTATIONSCALES")
    context_manager.set_reactors([root.dxf.handle])
    annot_scales.set_reactors([context_manager.dxf.handle])

    context_data = annot_scales.get("*A1")
    if not isinstance(context_data, DXFTagStorage):
        context_data = _new_tag_storage_object(
            doc,
            "ACDB_MTEXTATTRIBUTEOBJECTCONTEXTDATA_CLASS",
            annot_scales.dxf.handle,
            [
                [(100, "AcDbObjectContextData"), (70, 4), (290, 1)],
                [
                    (100, "AcDbAnnotScaleObjectContextData"),
                    (340, _default_annotation_scale_handle(doc)),
                    (70, 0),
                    (50, 0.0),
                    (10, (attdef.dxf.insert.x, attdef.dxf.insert.y)),
                    (11, (0.0, 0.0)),
                    (290, 0),
                ],
            ],
        )
        _set_owner_reactor(context_data, annot_scales.dxf.handle)
        annot_scales.add("*A1", context_data)


def _ensure_property_attdef_metadata(attdef, rep_index: int) -> None:
    _set_property_attdef_rep_etag(attdef, rep_index)
    _ensure_property_attdef_annotative_metadata(attdef)


def _get_property_attdefs(block: BlockLayout) -> tuple:
    return tuple(entity for entity in block if entity.dxftype() == "ATTDEF")


def _clone_property_attdefs_to_reference(reference: BlockLayout, dynamic_block: BlockLayout) -> None:
    existing_tags = {entity.dxf.tag for entity in reference if entity.dxftype() == "ATTDEF"}
    for attdef in _get_property_attdefs(dynamic_block):
        if attdef.dxf.tag in existing_tags:
            continue
        clone = reference.add_attdef(
            attdef.dxf.tag,
            insert=attdef.dxf.insert,
            text=attdef.dxf.text,
            height=attdef.dxf.height,
            rotation=attdef.dxf.get("rotation", 0.0),
            dxfattribs={
                "layer": attdef.dxf.layer,
                "color": attdef.dxf.color,
                "style": attdef.dxf.style,
                "flags": attdef.dxf.flags,
                "lock_position": attdef.dxf.get("lock_position", 1),
            },
        )
        clone.dxf.prompt = attdef.dxf.prompt



def _apply_visibility_state_to_block(
    block: BlockLayout,
    parameter: DynamicBlockVisibilityParameter,
    state: str,
    *,
    dynamic_block: Optional[BlockLayout] = None,
) -> None:
    if dynamic_block is None:
        dynamic_block = block

    visible_handles: tuple[str, ...] = ()
    for visibility_state in parameter.states:
        if visibility_state.name == state:
            visible_handles = visibility_state.entity_handles
            break
    if not visible_handles:
        return

    if block is dynamic_block:
        visible = set(visible_handles)
        for entity in block:
            if entity.dxf.handle in visible:
                entity.dxf.discard("invisible")
            else:
                entity.dxf.invisible = 1
        return

    base_entities = list(dynamic_block)
    ref_entities = list(block)
    handle_to_index = {
        entity.dxf.handle: index
        for index, entity in enumerate(base_entities)
        if entity.dxf.handle is not None
    }
    visible_indices = {handle_to_index[handle] for handle in visible_handles if handle in handle_to_index}
    for index, entity in enumerate(ref_entities):
        if index in visible_indices:
            entity.dxf.discard("invisible")
        else:
            entity.dxf.invisible = 1


def _apply_property_attdef_visibility(
    block: BlockLayout,
    dynamic_block: BlockLayout,
    state: str,
    first_state_name: str,
) -> None:
    property_tags = {attdef.dxf.tag for attdef in _get_property_attdefs(dynamic_block)}
    if not property_tags:
        return
    if get_dynamic_block_linear_parameters(dynamic_block):
        for entity in block:
            if entity.dxftype() != "ATTDEF":
                continue
            if entity.dxf.tag in property_tags:
                entity.dxf.discard("invisible")
        return
    visible = state == first_state_name
    for entity in block:
        if entity.dxftype() != "ATTDEF":
            continue
        if entity.dxf.tag not in property_tags:
            continue
        if visible:
            entity.dxf.discard("invisible")
        else:
            entity.dxf.invisible = 1


@dataclass(frozen=True)
class DynamicBlockVisibilityState:
    name: str
    entity_handles: tuple[str, ...] = ()


@dataclass(frozen=True)
class DynamicBlockVisibilityParameter:
    handle: str
    label: str
    parameter_name: str
    location: tuple[float, float, float]
    states: tuple[DynamicBlockVisibilityState, ...]
    all_entity_handles: tuple[str, ...] = ()


@dataclass(frozen=True)
class DynamicBlockLinearGrip:
    handle: str
    label: str
    location: tuple[float, float, float]
    offset: tuple[float, float, float]
    expr_id: int
    x_expr_id: int
    y_expr_id: int


@dataclass(frozen=True)
class DynamicBlockLinearParameter:
    handle: str
    label: str
    parameter_name: str
    description: str
    base_point: tuple[float, float, float]
    end_point: tuple[float, float, float]
    distance: float
    expr_id: int
    base_grip_handle: str = ""
    end_grip_handle: str = ""
    base_grip_label: str = ""
    end_grip_label: str = ""


@dataclass(frozen=True)
class DynamicBlockStretchActionTarget:
    entity_handle: str
    mode: int
    components: tuple[int, ...] = ()


@dataclass(frozen=True)
class DynamicBlockStretchAction:
    handle: str
    label: str
    action_location: tuple[float, float, float]
    x_expr_id: int
    x_name: str
    y_expr_id: int
    y_name: str
    selection_window: tuple[tuple[float, float, float], ...]
    dependency_handles: tuple[str, ...]
    targets: tuple[DynamicBlockStretchActionTarget, ...]


@dataclass(frozen=True)
class DynamicBlockPropertyColumn:
    source_handle: str
    source_dxftype: str
    name: str
    display_name: str = ""


@dataclass(frozen=True)
class DynamicBlockPropertyRow:
    index: int
    values: tuple[Any, ...]


@dataclass(frozen=True)
class DynamicBlockPropertiesTable:
    handle: str
    label: str
    table_name: str
    description: str
    location: tuple[float, float, float]
    grip_location: Optional[tuple[float, float, float]]
    columns: tuple[DynamicBlockPropertyColumn, ...]
    rows: tuple[DynamicBlockPropertyRow, ...]


@dataclass(frozen=True)
class DynamicBlockAssocVariable:
    handle: str
    name: str
    value: str
    evaluator_id: str
    expression: str
    raw_ints: tuple[int, ...] = ()


@dataclass(frozen=True)
class DynamicBlockAssocNetwork:
    handle: str
    block_record_handle: str
    block_name: str
    dictionary_handle: str
    variables: tuple[DynamicBlockAssocVariable, ...]


@dataclass(frozen=True)
class DynamicBlockPropertyCarrier:
    handle: str
    tag: str
    text: str
    invisible: int


@dataclass(frozen=True)
class DynamicBlockPropertyRepresentation:
    block_record_handle: str
    block_name: str
    is_active: bool
    invisible_flags: tuple[int, ...]
    carriers: tuple[DynamicBlockPropertyCarrier, ...]
    assoc_network: Optional[DynamicBlockAssocNetwork] = None


@dataclass(frozen=True)
class DynamicBlockPropertyRepresentationFamily:
    invisible_flags: tuple[int, ...]
    carrier_count: int
    carrier_texts: tuple[str, ...]
    carrier_visibility: tuple[int, ...]
    assoc_signature: tuple[tuple[str, str], ...]
    block_names: tuple[str, ...]


def get_dynamic_block_definition(
    insert: Insert, doc: Optional[Drawing] = None
) -> Optional[BlockLayout]:
    """Returns the dynamic block definition if the given block reference is
    referencing a dynamic block direct or indirect via an anonymous block.
    Returns ``None`` otherwise.
    """
    if doc is None:
        doc = insert.doc
        if doc is None:
            return None

    block = doc.blocks.get(insert.dxf.name)
    if block is None:
        return None

    block_record = block.block_record
    if is_dynamic_block_definition(block_record):
        return block  # direct dynamic block reference

    # is indirect dynamic block reference?
    handle = get_dynamic_block_record_handle(block_record)
    if not handle:
        return None  # lost reference to dynamic block definition
    dyn_block_record = doc.entitydb.get(handle)
    if dyn_block_record:
        return doc.blocks.get(dyn_block_record.dxf.name)
    return None


def get_dynamic_block_reference(
    insert: Insert, doc: Optional[Drawing] = None
) -> Optional[BlockLayout]:
    """Returns the anonymous block referenced by `insert` for a dynamic block.

    Returns ``None`` if the referenced block can not be resolved.
    """
    if doc is None:
        doc = insert.doc
        if doc is None:
            return None
    return doc.blocks.get(insert.dxf.name)


def is_dynamic_block_definition(block_record: BlockRecord) -> bool:
    """Return ``True`` if the given block record is a dynamic block definition."""
    return block_record.has_xdata(AcDbDynamicBlockGUID)


def get_dynamic_block_record_handle(block_record: BlockRecord) -> str:
    """Returns handle of the dynamic block record for an indirect dynamic block
    reference. Returns an empty string if the block record do not reference a dynamic
    block or the handle was not found.

    """
    try:  # check for indirect dynamic block reference
        xdata = block_record.get_xdata(AcDbBlockRepBTag)
    except const.DXFValueError:
        return ""  # not a dynamic block reference
    # get handle of dynamic block definition
    return xdata.get_first_value(1005, "")


def _get_enhanced_block_graph(block_record: BlockRecord) -> Optional[DXFTagStorage]:
    if not block_record.has_extension_dict:
        return None
    graph = block_record.get_extension_dict().dictionary.get("ACAD_ENHANCEDBLOCK")
    if isinstance(graph, DXFTagStorage) and graph.dxftype() == "ACAD_EVALUATION_GRAPH":
        return graph
    return None


def _iter_graph_owned_objects(graph: DXFTagStorage) -> Iterator[DXFTagStorage]:
    doc = graph.doc
    handle = graph.dxf.handle
    if doc is None or not handle:
        return iter(())
    return (
        entity
        for entity in doc.objects
        if isinstance(entity, DXFTagStorage) and entity.dxf.owner == handle
    )


def _parse_visibility_parameter(entity: DXFTagStorage) -> Optional[DynamicBlockVisibilityParameter]:
    if entity.dxftype() != "BLOCKVISIBILITYPARAMETER":
        return None
    try:
        element_tags = entity.xtags.get_subclass("AcDbBlockElement")
        location_tags = entity.xtags.get_subclass("AcDbBlock1PtParameter")
        visibility_tags = entity.xtags.get_subclass("AcDbBlockVisibilityParameter")
    except const.DXFKeyError:
        return None

    label = str(element_tags.get_first_value(300, ""))
    location = location_tags.get_first_value(1010, (0.0, 0.0, 0.0))
    parameter_name = str(visibility_tags.get_first_value(301, ""))
    all_entity_handles = tuple(str(value) for code, value in visibility_tags if code == 331)
    tags = list(visibility_tags)
    states: list[DynamicBlockVisibilityState] = []
    index = 0
    while index < len(tags):
        tag = tags[index]
        if tag.code != 303:
            index += 1
            continue
        state_name = str(tag.value)
        index += 1
        entity_handles: list[str] = []
        if index < len(tags) and tags[index].code == 94:
            index += 1
        while index < len(tags) and tags[index].code == 332:
            entity_handles.append(str(tags[index].value))
            index += 1
        if index < len(tags) and tags[index].code == 95:
            index += 1
        states.append(
            DynamicBlockVisibilityState(state_name, tuple(entity_handles))
        )
    return DynamicBlockVisibilityParameter(
        handle=entity.dxf.handle or "",
        label=label,
        parameter_name=parameter_name,
        location=(float(location[0]), float(location[1]), float(location[2])),
        states=tuple(states),
        all_entity_handles=all_entity_handles,
    )


def _point3d(value: Any) -> tuple[float, float, float]:
    if len(value) == 2:
        return (float(value[0]), float(value[1]), 0.0)
    return (float(value[0]), float(value[1]), float(value[2]))


def _eval_expr_id(entity: DXFTagStorage) -> int:
    try:
        return int(entity.xtags.get_subclass("AcDbEvalExpr").get_first_value(90, -1))
    except const.DXFKeyError:
        return -1


def _parse_linear_grip(entity: DXFTagStorage) -> Optional[DynamicBlockLinearGrip]:
    if entity.dxftype() != "BLOCKLINEARGRIP":
        return None
    try:
        element_tags = entity.xtags.get_subclass("AcDbBlockElement")
        grip_tags = entity.xtags.get_subclass("AcDbBlockGrip")
        linear_tags = entity.xtags.get_subclass("AcDbBlockLinearGrip")
    except const.DXFKeyError:
        return None
    location = grip_tags.get_first_value(1010, None)
    if location is None:
        return None
    return DynamicBlockLinearGrip(
        handle=entity.dxf.handle or "",
        label=str(element_tags.get_first_value(300, "")),
        location=_point3d(location),
        offset=(
            float(linear_tags.get_first_value(140, 0.0)),
            float(linear_tags.get_first_value(141, 0.0)),
            float(linear_tags.get_first_value(142, 0.0)),
        ),
        expr_id=_eval_expr_id(entity),
        x_expr_id=int(grip_tags.get_first_value(91, -1)),
        y_expr_id=int(grip_tags.get_first_value(92, -1)),
    )


def _parse_linear_parameter(
    entity: DXFTagStorage,
    grips_by_expr: dict[int, DynamicBlockLinearGrip],
) -> Optional[DynamicBlockLinearParameter]:
    if entity.dxftype() != "BLOCKLINEARPARAMETER":
        return None
    try:
        element_tags = entity.xtags.get_subclass("AcDbBlockElement")
        point_tags = entity.xtags.get_subclass("AcDbBlock2PtParameter")
        linear_tags = entity.xtags.get_subclass("AcDbBlockLinearParameter")
    except const.DXFKeyError:
        return None
    base_point = point_tags.get_first_value(1010, None)
    end_point = point_tags.get_first_value(1011, None)
    if base_point is None or end_point is None:
        return None
    grip_expr_ids = [int(tag.value) for tag in point_tags if tag.code == 91]
    base_grip = grips_by_expr.get(grip_expr_ids[0], None) if len(grip_expr_ids) > 0 else None
    end_grip = grips_by_expr.get(grip_expr_ids[1], None) if len(grip_expr_ids) > 1 else None
    return DynamicBlockLinearParameter(
        handle=entity.dxf.handle or "",
        label=str(element_tags.get_first_value(300, "")),
        parameter_name=str(linear_tags.get_first_value(305, "")),
        description=str(linear_tags.get_first_value(306, "")),
        base_point=_point3d(base_point),
        end_point=_point3d(end_point),
        distance=float(linear_tags.get_first_value(140, 0.0)),
        expr_id=_eval_expr_id(entity),
        base_grip_handle=base_grip.handle if base_grip is not None else "",
        end_grip_handle=end_grip.handle if end_grip is not None else "",
        base_grip_label=base_grip.label if base_grip is not None else "",
        end_grip_label=end_grip.label if end_grip is not None else "",
    )


def _parse_stretch_action(entity: DXFTagStorage) -> Optional[DynamicBlockStretchAction]:
    if entity.dxftype() != "BLOCKSTRETCHACTION":
        return None
    try:
        element_tags = entity.xtags.get_subclass("AcDbBlockElement")
        action_tags = entity.xtags.get_subclass("AcDbBlockAction")
        stretch_tags = list(entity.xtags.get_subclass("AcDbBlockStretchAction"))
    except const.DXFKeyError:
        return None
    action_location = action_tags.get_first_value(1010, None)
    if action_location is None:
        return None
    selection_window = tuple(_point3d(tag.value) for tag in stretch_tags if tag.code == 1011)
    dependency_handles = tuple(str(tag.value) for tag in action_tags if tag.code == 330)
    x_expr_id = int(next((tag.value for tag in stretch_tags if tag.code == 92), -1))
    y_expr_id = int(next((tag.value for tag in stretch_tags if tag.code == 93), -1))
    x_name = str(next((tag.value for tag in stretch_tags if tag.code == 301), ""))
    y_name = str(next((tag.value for tag in stretch_tags if tag.code == 302), ""))
    targets: list[DynamicBlockStretchActionTarget] = []
    index = 0
    while index < len(stretch_tags):
        if stretch_tags[index].code != 331:
            index += 1
            continue
        entity_handle = str(stretch_tags[index].value)
        index += 1
        mode = 0
        if index < len(stretch_tags) and stretch_tags[index].code == 74:
            mode = int(stretch_tags[index].value)
            index += 1
        components: list[int] = []
        while index < len(stretch_tags) and stretch_tags[index].code == 94:
            components.append(int(stretch_tags[index].value))
            index += 1
        targets.append(
            DynamicBlockStretchActionTarget(
                entity_handle=entity_handle,
                mode=mode,
                components=tuple(components),
            )
        )
    return DynamicBlockStretchAction(
        handle=entity.dxf.handle or "",
        label=str(element_tags.get_first_value(300, "")),
        action_location=_point3d(action_location),
        x_expr_id=x_expr_id,
        x_name=x_name,
        y_expr_id=y_expr_id,
        y_name=y_name,
        selection_window=selection_window,
        dependency_handles=dependency_handles,
        targets=tuple(targets),
    )


def _parse_block_properties_table_grip(entity: DXFTagStorage) -> Optional[tuple[float, float, float]]:
    if entity.dxftype() != "BLOCKPROPERTIESTABLEGRIP":
        return None
    try:
        grip_tags = entity.xtags.get_subclass("AcDbBlockGrip")
    except const.DXFKeyError:
        return None
    location = grip_tags.get_first_value(1010, None)
    if location is None:
        return None
    return (float(location[0]), float(location[1]), float(location[2]))


def _resolve_property_column(table: DXFTagStorage, source_handle: str, column_name: str) -> DynamicBlockPropertyColumn:
    doc = table.doc
    source = doc.entitydb.get(source_handle) if doc is not None else None
    source_dxftype = source.dxftype() if source is not None else "UNKNOWN"
    display_name = column_name
    name = column_name
    if source_dxftype == "ATTDEF":
        name = source.dxf.get("tag", "")
        if not display_name:
            display_name = source.dxf.get("text", "")
    elif source_dxftype == "BLOCKVISIBILITYPARAMETER":
        visibility = _parse_visibility_parameter(source) if isinstance(source, DXFTagStorage) else None
        if not name and visibility is not None:
            name = visibility.parameter_name
        if not display_name and visibility is not None:
            display_name = visibility.label
    if not name:
        name = source_handle
    return DynamicBlockPropertyColumn(
        source_handle=source_handle,
        source_dxftype=source_dxftype,
        name=name,
        display_name=display_name,
    )


def _convert_property_cell_value(tag) -> Any:
    if tag.code in (300, 301, 302, 303, 1):
        return str(tag.value)
    if tag.code in (40, 41, 42, 43, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149):
        return float(tag.value)
    if 60 <= tag.code <= 99 or 170 <= tag.code <= 299 or 1070 <= tag.code <= 1071:
        return int(tag.value)
    return tag.value


def _parse_block_properties_table(entity: DXFTagStorage) -> Optional[DynamicBlockPropertiesTable]:
    if entity.dxftype() != "BLOCKPROPERTIESTABLE":
        return None
    try:
        element_tags = entity.xtags.get_subclass("AcDbBlockElement")
        location_tags = entity.xtags.get_subclass("AcDbBlock1PtParameter")
        table_tags = list(entity.xtags.get_subclass("AcDbBlockPropertiesTable"))[1:]
    except const.DXFKeyError:
        return None

    label = str(element_tags.get_first_value(300, ""))
    location = location_tags.get_first_value(1010, (0.0, 0.0, 0.0))
    index = 0
    if index >= len(table_tags) or table_tags[index].code != 90:
        return None
    index += 1  # table version marker
    table_name = str(table_tags[index].value) if index < len(table_tags) and table_tags[index].code == 300 else ""
    index += 1
    description = str(table_tags[index].value) if index < len(table_tags) and table_tags[index].code == 301 else ""
    index += 1
    if index >= len(table_tags) or table_tags[index].code != 91:
        return None
    column_count = int(table_tags[index].value)
    index += 1

    columns: list[DynamicBlockPropertyColumn] = []
    for _ in range(column_count):
        if index >= len(table_tags) or table_tags[index].code != 340:
            return None
        source_handle = str(table_tags[index].value)
        index += 1
        column_name = ""
        while index < len(table_tags):
            tag = table_tags[index]
            index += 1
            if tag.code == 301:
                column_name = str(tag.value)
            if tag.code == 340 and str(tag.value) == "0":
                break
        columns.append(_resolve_property_column(entity, source_handle, column_name))

    if index >= len(table_tags) or table_tags[index].code != 92:
        return None
    row_count = int(table_tags[index].value)
    index += 1

    rows: list[DynamicBlockPropertyRow] = []
    for _ in range(row_count):
        if index >= len(table_tags) or table_tags[index].code != 90:
            break
        row_index = int(table_tags[index].value)
        index += 1
        values: list[Any] = []
        for _column in range(column_count):
            if index >= len(table_tags) or table_tags[index].code != 170:
                break
            index += 1  # value type marker, currently ignored
            if index >= len(table_tags):
                break
            value_tag = table_tags[index]
            index += 1
            values.append(_convert_property_cell_value(value_tag))
        rows.append(DynamicBlockPropertyRow(index=row_index, values=tuple(values)))

    grip_location = None
    graph = entity.doc.entitydb.get(entity.dxf.owner) if entity.doc is not None else None
    if isinstance(graph, DXFTagStorage):
        for owned in _iter_graph_owned_objects(graph):
            grip_location = _parse_block_properties_table_grip(owned)
            if grip_location is not None:
                break

    return DynamicBlockPropertiesTable(
        handle=entity.dxf.handle or "",
        label=label,
        table_name=table_name,
        description=description,
        location=(float(location[0]), float(location[1]), float(location[2])),
        grip_location=grip_location,
        columns=tuple(columns),
        rows=tuple(rows),
    )


def _resolve_dynamic_block_record(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> Optional[BlockRecord]:
    if isinstance(source, Insert):
        block = get_dynamic_block_definition(source, doc)
        return block.block_record if block is not None else None
    if hasattr(source, "block_record"):
        return source.block_record  # BlockLayout
    return source


def get_dynamic_block_visibility_parameter(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> Optional[DynamicBlockVisibilityParameter]:
    block_record = _resolve_dynamic_block_record(source, doc)
    if block_record is None:
        return None
    graph = _get_enhanced_block_graph(block_record)
    if graph is None:
        return None
    for entity in _iter_graph_owned_objects(graph):
        parameter = _parse_visibility_parameter(entity)
        if parameter is not None:
            return parameter
    return None


def get_dynamic_block_visibility_states(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[str, ...]:
    parameter = get_dynamic_block_visibility_parameter(source, doc)
    if parameter is None:
        return ()
    return tuple(state.name for state in parameter.states)


def _iter_visibility_state_xrecords(insert: Insert) -> Iterator[XRecord]:
    if not insert.has_extension_dict:
        return iter(())
    rep = insert.get_extension_dict().dictionary.get("AcDbBlockRepresentation")
    if not isinstance(rep, Dictionary):
        return iter(())
    appdata_cache = rep.get("AppDataCache")
    if not isinstance(appdata_cache, Dictionary):
        return iter(())
    enhanced = appdata_cache.get("ACAD_ENHANCEDBLOCKDATA")
    if not isinstance(enhanced, Dictionary):
        return iter(())

    def iter_items(dictionary: Dictionary) -> Iterator[XRecord]:
        for _, value in dictionary.items():
            if isinstance(value, XRecord):
                yield value
            elif isinstance(value, Dictionary):
                yield from iter_items(value)

    return iter_items(enhanced)


def get_dynamic_block_visibility_state(
    insert: Insert, doc: Optional[Drawing] = None
) -> str:
    names = set(get_dynamic_block_visibility_states(insert, doc))
    if not names:
        return ""
    for xrecord in _iter_visibility_state_xrecords(insert):
        state_name = xrecord.tags.get_first_value(1, "")
        if state_name in names:
            return str(state_name)
    return ""


def get_dynamic_block_visibility_state_handles(
    source: Union[Insert, BlockLayout, BlockRecord],
    state: str = "",
    doc: Optional[Drawing] = None,
) -> tuple[str, ...]:
    parameter = get_dynamic_block_visibility_parameter(source, doc)
    if parameter is None or not parameter.states:
        return ()
    if not state and isinstance(source, Insert):
        state = get_dynamic_block_visibility_state(source, doc)
    for visibility_state in parameter.states:
        if visibility_state.name == state:
            return visibility_state.entity_handles
    return ()


def _resolve_block_layout(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> Optional[BlockLayout]:
    if isinstance(source, Insert):
        return get_dynamic_block_reference(source, doc)
    if hasattr(source, "block_record"):
        return source
    if doc is None:
        doc = source.doc
    if doc is None:
        return None
    return doc.blocks.get(source.dxf.name)


def get_dynamic_block_visibility_entities(
    source: Union[Insert, BlockLayout, BlockRecord],
    state: str = "",
    doc: Optional[Drawing] = None,
) -> tuple[DXFEntity, ...]:
    handles = get_dynamic_block_visibility_state_handles(source, state, doc)
    if not handles:
        return ()
    if isinstance(source, Insert):
        base_block = get_dynamic_block_definition(source, doc)
        ref_block = get_dynamic_block_reference(source, doc)
        if base_block is None or ref_block is None:
            return ()
        base_entities = list(base_block)
        ref_entities = list(ref_block)
        handle_to_index = {
            entity.dxf.handle: index
            for index, entity in enumerate(base_entities)
            if entity.dxf.handle is not None
        }
        result: list[DXFEntity] = []
        for handle in handles:
            index = handle_to_index.get(handle)
            if index is None or index >= len(ref_entities):
                continue
            result.append(ref_entities[index])
        return tuple(result)

    block = _resolve_block_layout(source, doc)
    if block is None:
        return ()
    entitydb = block.doc.entitydb if block.doc is not None else None
    if entitydb is None:
        return ()
    result: list[DXFEntity] = []
    for handle in handles:
        entity = entitydb.get(handle)
        if entity is not None:
            result.append(entity)
    return tuple(result)


def _get_dynamic_graph_owned_objects(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DXFTagStorage, ...]:
    block_record = _resolve_dynamic_block_record(source, doc)
    if block_record is None:
        return ()
    graph = _get_enhanced_block_graph(block_record)
    if graph is None:
        return ()
    return tuple(_iter_graph_owned_objects(graph))


def get_dynamic_block_linear_grips(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockLinearGrip, ...]:
    result: list[DynamicBlockLinearGrip] = []
    for entity in _get_dynamic_graph_owned_objects(source, doc):
        grip = _parse_linear_grip(entity)
        if grip is not None:
            result.append(grip)
    return tuple(result)


def get_dynamic_block_linear_parameters(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockLinearParameter, ...]:
    grips_by_expr = {grip.expr_id: grip for grip in get_dynamic_block_linear_grips(source, doc)}
    result: list[DynamicBlockLinearParameter] = []
    for entity in _get_dynamic_graph_owned_objects(source, doc):
        parameter = _parse_linear_parameter(entity, grips_by_expr)
        if parameter is not None:
            result.append(parameter)
    return tuple(result)


def get_dynamic_block_stretch_actions(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockStretchAction, ...]:
    result: list[DynamicBlockStretchAction] = []
    for entity in _get_dynamic_graph_owned_objects(source, doc):
        action = _parse_stretch_action(entity)
        if action is not None:
            result.append(action)
    return tuple(result)


def get_dynamic_block_properties_table(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> Optional[DynamicBlockPropertiesTable]:
    for entity in _get_dynamic_graph_owned_objects(source, doc):
        table = _parse_block_properties_table(entity)
        if table is not None:
            return table
    return None


def get_dynamic_block_property_columns(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockPropertyColumn, ...]:
    table = get_dynamic_block_properties_table(source, doc)
    if table is None:
        return ()
    return table.columns


def get_dynamic_block_property_rows(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockPropertyRow, ...]:
    table = get_dynamic_block_properties_table(source, doc)
    if table is None:
        return ()
    return table.rows


def _iter_dynamic_reference_block_records(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> Iterator[BlockRecord]:
    block_record = _resolve_dynamic_block_record(source, doc)
    if block_record is None:
        return iter(())
    doc = block_record.doc
    handle = block_record.dxf.handle
    if doc is None or not handle:
        return iter(())

    def iterator() -> Iterator[BlockRecord]:
        for candidate in doc.block_records:
            if candidate is block_record:
                continue
            if get_dynamic_block_record_handle(candidate) == handle:
                yield candidate

    return iterator()


def _iter_assoc_network_dictionaries(block_record: BlockRecord) -> Iterator[Dictionary]:
    doc = block_record.doc
    handle = block_record.dxf.handle
    if doc is None or not handle:
        return iter(())

    def iterator() -> Iterator[Dictionary]:
        for obj in doc.objects:
            if not isinstance(obj, Dictionary) or obj.dxf.owner != handle:
                continue
            if "ACAD_ASSOCNETWORK" in obj:
                yield obj

    return iterator()


def _resolve_assoc_network(dictionary: Dictionary):
    target = dictionary.get("ACAD_ASSOCNETWORK")
    if target is None:
        return None
    if isinstance(target, Dictionary):
        target = target.get("ACAD_ASSOCNETWORK")
    return target if isinstance(target, DXFTagStorage) and target.dxftype() == "ACDBASSOCNETWORK" else None


def _parse_assoc_variable(entity: DXFTagStorage) -> Optional[DynamicBlockAssocVariable]:
    if entity.dxftype() != "ACDBASSOCVARIABLE":
        return None
    try:
        tags = entity.xtags.get_subclass("AcDbAssocVariable")
    except const.DXFKeyError:
        return None
    strings = [str(tag.value) for tag in tags if tag.code == 1]
    ints = tuple(int(tag.value) for tag in tags if tag.code == 90)
    name = strings[0] if len(strings) else ""
    value = strings[1] if len(strings) > 1 else ""
    evaluator_id = strings[2] if len(strings) > 2 else ""
    expression = strings[3] if len(strings) > 3 else ""
    return DynamicBlockAssocVariable(
        handle=entity.dxf.handle or "",
        name=name,
        value=value,
        evaluator_id=evaluator_id,
        expression=expression,
        raw_ints=ints,
    )


def get_dynamic_block_property_assoc_networks(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockAssocNetwork, ...]:
    result: list[DynamicBlockAssocNetwork] = []
    for block_record in _iter_dynamic_reference_block_records(source, doc):
        for dictionary in _iter_assoc_network_dictionaries(block_record):
            network = _resolve_assoc_network(dictionary)
            if network is None:
                continue
            variables: list[DynamicBlockAssocVariable] = []
            if len(network.xtags.subclasses) > 2:
                for code, value in network.xtags.subclasses[2]:
                    if code != 360:
                        continue
                    child = network.doc.entitydb.get(str(value)) if network.doc is not None else None
                    if not isinstance(child, DXFTagStorage):
                        continue
                    variable = _parse_assoc_variable(child)
                    if variable is not None:
                        variables.append(variable)
            result.append(
                DynamicBlockAssocNetwork(
                    handle=network.dxf.handle or "",
                    block_record_handle=block_record.dxf.handle or "",
                    block_name=block_record.dxf.name,
                    dictionary_handle=dictionary.dxf.handle or "",
                    variables=tuple(variables),
                )
            )
    return tuple(result)


def get_dynamic_block_property_representations(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockPropertyRepresentation, ...]:
    assoc_by_block = {
        network.block_record_handle: network
        for network in get_dynamic_block_property_assoc_networks(source, doc)
    }
    active_names: set[str] = set()
    block_record = _resolve_dynamic_block_record(source, doc)
    if block_record is not None and block_record.doc is not None:
        doc = block_record.doc
        for ins in doc.modelspace().query("INSERT"):
            base = get_dynamic_block_definition(ins, doc)
            if base is not None and base.block_record is block_record:
                active_names.add(ins.dxf.name)
    result: list[DynamicBlockPropertyRepresentation] = []
    for block_record in _iter_dynamic_reference_block_records(source, doc):
        block = _resolve_block_layout(block_record, doc)
        if block is None:
            continue
        carriers = tuple(
            DynamicBlockPropertyCarrier(
                handle=entity.dxf.handle or "",
                tag=entity.dxf.tag,
                text=entity.dxf.text,
                invisible=int(entity.dxf.get("invisible", 0)),
            )
            for entity in block
            if entity.dxftype() == "ATTDEF"
        )
        if not carriers and block_record.dxf.handle not in assoc_by_block:
            continue
        result.append(
            DynamicBlockPropertyRepresentation(
                block_record_handle=block_record.dxf.handle or "",
                block_name=block_record.dxf.name,
                is_active=block_record.dxf.name in active_names,
                invisible_flags=tuple(int(entity.dxf.get("invisible", 0)) for entity in block),
                carriers=carriers,
                assoc_network=assoc_by_block.get(block_record.dxf.handle or ""),
            )
        )
    return tuple(result)


def get_dynamic_block_property_representation_families(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> tuple[DynamicBlockPropertyRepresentationFamily, ...]:
    families: dict[
        tuple[tuple[int, ...], int, tuple[str, ...], tuple[int, ...], tuple[tuple[str, str], ...]],
        list[str],
    ] = {}
    for rep in get_dynamic_block_property_representations(source, doc):
        assoc_signature: tuple[tuple[str, str], ...] = ()
        if rep.assoc_network is not None:
            assoc_signature = tuple((var.name, var.value) for var in rep.assoc_network.variables)
        key = (
            rep.invisible_flags,
            len(rep.carriers),
            tuple(carrier.text for carrier in rep.carriers),
            tuple(carrier.invisible for carrier in rep.carriers),
            assoc_signature,
        )
        families.setdefault(key, []).append(rep.block_name)

    result: list[DynamicBlockPropertyRepresentationFamily] = []
    for key, names in families.items():
        invisible_flags, carrier_count, carrier_texts, carrier_visibility, assoc_signature = key
        result.append(
            DynamicBlockPropertyRepresentationFamily(
                invisible_flags=invisible_flags,
                carrier_count=carrier_count,
                carrier_texts=carrier_texts,
                carrier_visibility=carrier_visibility,
                assoc_signature=assoc_signature,
                block_names=tuple(names),
            )
        )
    return tuple(result)


def _delete_graph_stack(block_record: BlockRecord) -> None:
    graph = _get_enhanced_block_graph(block_record)
    if graph is None:
        return
    doc = block_record.doc
    if doc is None:
        return
    xdict = block_record.get_extension_dict().dictionary
    for entity in list(_iter_graph_owned_objects(graph)):
        doc.objects.delete_entity(entity)
    xdict.discard("ACAD_ENHANCEDBLOCK")
    doc.objects.delete_entity(graph)
    purge = xdict.get("AcDbDynamicBlockRoundTripPurgePreventer")
    if isinstance(purge, DXFTagStorage):
        xdict.discard("AcDbDynamicBlockRoundTripPurgePreventer")
        doc.objects.delete_entity(purge)


def _delete_assoc_networks(block_record: BlockRecord) -> None:
    doc = block_record.doc
    if doc is None:
        return
    for obj in list(doc.objects):
        if isinstance(obj, Dictionary) and obj.dxf.owner == block_record.dxf.handle:
            if "ACAD_ASSOCNETWORK" in obj:
                doc.objects.delete_entity(obj)


def _delete_owned_object_tree(doc: Drawing, owner_handle: str) -> None:
    if not owner_handle:
        return
    children = [entity for entity in doc.objects if entity.dxf.owner == owner_handle]
    for entity in children:
        handle = entity.dxf.handle or ""
        if isinstance(entity, Dictionary) and entity.is_hard_owner:
            doc.objects.delete_entity(entity)
            continue
        _delete_owned_object_tree(doc, handle)
        if entity.is_alive:
            doc.objects.delete_entity(entity)


def _delete_hidden_dynamic_support_blocks(block_record: BlockRecord) -> None:
    doc = block_record.doc
    if doc is None:
        return
    to_delete: list[str] = []
    for candidate in _iter_dynamic_reference_block_records(block_record, doc):
        if candidate.blkref_handles:
            continue
        _delete_owned_object_tree(doc, candidate.dxf.handle or "")
        to_delete.append(candidate.dxf.name)
    for name in to_delete:
        if name in doc.blocks:
            doc.blocks.delete_block(name, safe=False)


def _clone_non_attdef_entities(source_block: BlockLayout, target_block: BlockLayout) -> None:
    for entity in source_block:
        if entity.dxftype() == "ATTDEF":
            continue
        target_block.add_entity(entity.copy())


def _clone_property_attdef(source_attdef, target_block: BlockLayout, *, text: str, invisible: bool) -> None:
    clone = target_block.add_attdef(
        source_attdef.dxf.tag,
        insert=source_attdef.dxf.insert,
        text=text,
        height=source_attdef.dxf.height,
        rotation=source_attdef.dxf.get("rotation", 0.0),
        dxfattribs={
            "layer": source_attdef.dxf.layer,
            "color": source_attdef.dxf.color,
            "style": source_attdef.dxf.style,
            "flags": source_attdef.dxf.flags,
            "lock_position": source_attdef.dxf.get("lock_position", 1),
        },
    )
    clone.dxf.prompt = source_attdef.dxf.prompt
    if invisible:
        clone.dxf.invisible = 1
    else:
        clone.dxf.discard("invisible")


def _set_property_attdef_reactors(block: BlockLayout, table_handle: str) -> None:
    for entity in block:
        if entity.dxftype() == "ATTDEF":
            entity.set_reactors([table_handle])


def _assoc_variable_tags(network_handle: str, variable_index: int, name: str, value: str) -> list[list[tuple[int, Any]]]:
    stored_value = value
    int_value = 0
    if isinstance(value, str) and value.startswith("VAL "):
        try:
            int_value = int(value.split()[-1])
            stored_value = str(int_value)
        except ValueError:
            int_value = 0
    else:
        try:
            int_value = int(value)
            stored_value = str(int_value)
        except (TypeError, ValueError):
            int_value = 0
    return [
        [
            (100, "AcDbAssocAction"),
            (90, 2),
            (90, 0),
            (330, network_handle),
            (360, "0"),
            (90, variable_index),
            (90, 0),
            (90, 0),
            (90, 0),
            (90, 0),
            (90, 0),
            (90, 0),
        ],
        [
            (100, "AcDbAssocVariable"),
            (90, 2),
            (1, name),
            (1, stored_value),
            (1, "AcDbCalc:1.0"),
            (1, ""),
            (90, int_value),
            (290, 0),
            (290, 0),
            (90, 0),
        ],
    ]


def _ensure_root_assoc_network(doc: Drawing) -> DXFTagStorage:
    rootdict = doc.rootdict
    outer = rootdict.get("ACAD_ASSOCNETWORK")
    if not isinstance(outer, Dictionary):
        outer = rootdict.add_new_dict("ACAD_ASSOCNETWORK")
        outer.set_reactors([rootdict.dxf.handle])
    network = _resolve_assoc_network(outer)
    if isinstance(network, DXFTagStorage):
        return network
    network = _new_tag_storage_object(
        doc,
        "ACDBASSOCNETWORK",
        outer.dxf.handle,
        [
            [
                (100, "AcDbAssocAction"),
                (90, 2),
                (90, 0),
                (330, "0"),
                (360, "0"),
                (90, 0),
                (90, 0),
                (90, 0),
                (90, 0),
                (90, 0),
                (90, 0),
                (90, 0),
            ],
            [(100, "AcDbAssocNetwork"), (90, 0), (90, 6), (90, 0), (90, 0)],
        ],
    )
    _set_owner_reactor(network, outer.dxf.handle)
    outer.add("ACAD_ASSOCNETWORK", network)
    return network


def _set_root_assoc_children(network: DXFTagStorage, child_handles: Sequence[str]) -> None:
    sub = network.xtags.get_subclass("AcDbAssocNetwork")
    tags = [(100, "AcDbAssocNetwork"), (90, 0), (90, len(child_handles) + 6), (90, len(child_handles))]
    tags.extend((330, handle) for handle in child_handles)
    tags.append((90, 0))
    sub.clear()
    from ezdxf.lldxf.types import dxftag

    sub.extend(dxftag(code, value) for code, value in tags)


def _new_assoc_network_bundle(
    block_record: BlockRecord,
    root_network_handle: str,
    variables: Sequence[tuple[str, str]],
    *,
    action_index: int,
) -> DynamicBlockAssocNetwork:
    doc = block_record.doc
    assert doc is not None
    outer = doc.objects.add_dictionary(owner=block_record.dxf.handle)
    inner = outer.add_new_dict("ACAD_ASSOCNETWORK")
    inner.set_reactors([outer.dxf.handle])
    network = _new_tag_storage_object(
        doc,
        "ACDBASSOCNETWORK",
        inner.dxf.handle,
        [
            [
                (100, "AcDbAssocAction"),
                (90, 2),
                (90, 0),
                (330, root_network_handle),
                (360, "0"),
                (90, action_index),
                (90, 0),
                (90, 0),
                (90, 0),
                (90, 0),
                (90, 0),
                (90, 0),
            ],
            [
                (100, "AcDbAssocNetwork"),
                (90, 0),
                (90, len(variables)),
                (90, len(variables)),
                *[(360, "0") for _ in variables],
                (90, 0),
            ],
        ],
    )
    _set_owner_reactor(network, inner.dxf.handle)
    inner.add("ACAD_ASSOCNETWORK", network)
    network_sub = network.xtags.get_subclass("AcDbAssocNetwork")
    created_variables: list[DynamicBlockAssocVariable] = []
    handles: list[str] = []
    for index, (name, value) in enumerate(variables, start=1):
        entity = _new_tag_storage_object(
            doc,
            "ACDBASSOCVARIABLE",
            network.dxf.handle,
            _assoc_variable_tags(network.dxf.handle, index, name, value),
        )
        handles.append(entity.dxf.handle)
        created_variables.append(
            DynamicBlockAssocVariable(
                handle=entity.dxf.handle or "",
                name=name,
                value=value,
                evaluator_id="AcDbCalc:1.0",
                expression="",
                raw_ints=(2, int(value.split()[-1]) if value.startswith("VAL ") else 0, 0),
            )
        )
    tags = [(100, "AcDbAssocNetwork"), (90, 0), (90, len(variables)), (90, len(variables))]
    tags.extend((360, handle) for handle in handles)
    tags.append((90, 0))
    network_sub.clear()
    from ezdxf.lldxf.types import dxftag

    network_sub.extend(dxftag(code, value) for code, value in tags)
    return DynamicBlockAssocNetwork(
        handle=network.dxf.handle or "",
        block_record_handle=block_record.dxf.handle or "",
        block_name=block_record.dxf.name,
        dictionary_handle=outer.dxf.handle or "",
        variables=tuple(created_variables),
    )


def _resolve_property_table_columns(
    block: BlockLayout,
    table: DynamicBlockPropertiesTable,
    visibility: DynamicBlockVisibilityParameter,
) -> tuple[DynamicBlockPropertyColumn, ...]:
    doc = block.doc
    assert doc is not None
    entitydb = doc.entitydb
    columns: list[DynamicBlockPropertyColumn] = []
    attdef_index = 1
    for column in table.columns:
        source_handle = column.source_handle
        source_dxftype = column.source_dxftype or "ATTDEF"
        name = column.name
        display_name = column.display_name
        if source_dxftype == "BLOCKVISIBILITYPARAMETER":
            source_handle = visibility.handle
            display_name = display_name or name or "VisibilityState"
            name = name or visibility.parameter_name
        elif source_dxftype == "ATTDEF":
            attdef = entitydb.get(source_handle) if source_handle else None
            if attdef is None:
                x = table.location[0] + 1.5 + (attdef_index % 2) * 0.25
                y = table.location[1] - 4.5 * attdef_index - (attdef_index % 2) * 0.3
                attdef = block.add_attdef(
                    name or f"PARAM_{attdef_index}",
                    insert=(x, y),
                    text=table.table_name or "Block Table1",
                    height=2.5,
                    dxfattribs={"flags": 1, "lock_position": 1},
                )
                source_handle = attdef.dxf.handle
            else:
                source_handle = attdef.dxf.handle
            name = name or attdef.dxf.get("tag", source_handle)
            display_name = display_name or attdef.dxf.get("text", "")
            attdef_index += 1
        columns.append(
            DynamicBlockPropertyColumn(
                source_handle=source_handle,
                source_dxftype=source_dxftype,
                name=name or source_handle,
                display_name=display_name,
            )
        )
    return tuple(columns)


def _build_block_properties_table_subclass(
    table: DynamicBlockPropertiesTable,
    columns: Sequence[DynamicBlockPropertyColumn],
) -> list[tuple[int, Any]]:
    tags: list[tuple[int, Any]] = [
        (100, "AcDbBlockPropertiesTable"),
        (90, 2),
        (300, table.table_name),
        (301, table.description),
        (91, len(columns)),
    ]
    for column in columns:
        value_type = 6 if column.source_dxftype == "BLOCKVISIBILITYPARAMETER" else 0
        editable = 0 if column.source_dxftype == "BLOCKVISIBILITYPARAMETER" else 1
        tags.extend(
            [
                (340, column.source_handle),
                (170, 0),
                (171, -1),
                (300, ""),
                (301, column.display_name if column.source_dxftype == "BLOCKVISIBILITYPARAMETER" else ""),
                (90, value_type),
                (170, -9999),
                (170, -9999),
                (290, 0),
                (291, 1),
                (292, 1),
                (293, 0),
                (294, editable),
                (302, ""),
                (340, "0"),
            ]
        )
    tags.append((92, len(table.rows)))
    for row in table.rows:
        tags.append((90, row.index))
        for value in row.values:
            tags.append((170, 1))
            tags.append((300, str(value)))
    tags.extend([(93, len(table.rows)), (290, 0), (291, 1), (292, 0)])
    return tags


def _build_property_visibility_parameter_subclass(
    visibility: DynamicBlockVisibilityParameter,
    properties_table_handle: str,
    properties_grip_handle: str,
    *,
    extra_state_refs: Sequence[Sequence[str]] = (),
    all_handles: Optional[Sequence[str]] = None,
) -> list[tuple[int, Any]]:
    if all_handles is None:
        all_handles = visibility.all_entity_handles or tuple(
            handle
            for state in visibility.states
            for handle in state.entity_handles
            if handle
        )
    tags: list[tuple[int, Any]] = [
        (100, "AcDbBlockVisibilityParameter"),
        (281, 1),
        (301, visibility.parameter_name),
        (302, ""),
        (91, 0),
        (93, len(all_handles)),
        *[(331, handle) for handle in all_handles],
        (92, len(visibility.states)),
    ]
    for index, state in enumerate(visibility.states):
        tags.extend(
            [
                (303, state.name),
                (94, len(state.entity_handles)),
                *[(332, handle) for handle in state.entity_handles],
            ]
        )
        refs = [properties_grip_handle]
        if index == 0 and properties_table_handle:
            refs.append(properties_table_handle)
        if index < len(extra_state_refs):
            refs.extend(extra_state_refs[index])
        refs = [handle for handle in refs if handle and handle != "0"]
        tags.extend([(95, len(refs)), *[(333, handle) for handle in refs]])
    return tags


def _unique_handles(handles: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for handle in handles:
        value = str(handle)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def _augment_visibility_with_property_attdefs(
    visibility: DynamicBlockVisibilityParameter,
    attdefs: Sequence[Any],
) -> DynamicBlockVisibilityParameter:
    property_handles = tuple(attdef.dxf.handle for attdef in attdefs if attdef.dxf.handle)
    if not property_handles:
        return visibility
    states = tuple(
        DynamicBlockVisibilityState(
            state.name,
            _unique_handles([*state.entity_handles, *property_handles]),
        )
        for state in visibility.states
    )
    all_handles = _unique_handles([*(visibility.all_entity_handles or ()), *property_handles])
    if not all_handles:
        all_handles = _unique_handles(
            [handle for state in states for handle in state.entity_handles]
        )
    return DynamicBlockVisibilityParameter(
        handle=visibility.handle,
        label=visibility.label,
        parameter_name=visibility.parameter_name,
        location=visibility.location,
        states=states,
        all_entity_handles=all_handles,
    )


def _replace_subclass_tags(subclass, tags: Sequence[tuple[int, Any]]) -> None:
    from ezdxf.lldxf.types import dxftag

    subclass.clear()
    subclass.extend(dxftag(code, value) for code, value in tags)


def _patch_eval_graph_handles(graph: DXFTagStorage, handles: Sequence[str]) -> None:
    eval_graph = graph.xtags.get_subclass("AcDbEvalGraph")
    from ezdxf.lldxf.types import dxftag

    handle_index = 0
    for index, tag in enumerate(eval_graph):
        if tag.code == 360 and handle_index < len(handles):
            eval_graph[index] = dxftag(360, handles[handle_index])
            handle_index += 1


def _build_linear_eval_graph_subclass() -> list[tuple[int, Any]]:
    return [
        (100, "AcDbEvalGraph"),
        (96, 52),
        (97, 52),
        (91, 0),
        (93, 32),
        (95, 6),
        (360, "0"),
        (92, 3),
        (92, 3),
        (92, 4),
        (92, 4),
        (91, 1),
        (93, 32),
        (95, 16),
        (360, "0"),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, -1),
        (91, 2),
        (93, 32),
        (95, 32),
        (360, "0"),
        (92, 0),
        (92, 4),
        (92, 1),
        (92, 3),
        (91, 3),
        (93, 32),
        (95, 33),
        (360, "0"),
        (92, -1),
        (92, -1),
        (92, 0),
        (92, 0),
        (91, 4),
        (93, 32),
        (95, 34),
        (360, "0"),
        (92, 1),
        (92, 1),
        (92, -1),
        (92, -1),
        (91, 5),
        (93, 32),
        (95, 35),
        (360, "0"),
        (92, 2),
        (92, 2),
        (92, -1),
        (92, -1),
        (91, 6),
        (93, 32),
        (95, 45),
        (360, "0"),
        (92, 7),
        (92, 10),
        (92, 5),
        (92, 11),
        (91, 7),
        (93, 32),
        (95, 46),
        (360, "0"),
        (92, -1),
        (92, -1),
        (92, 7),
        (92, 7),
        (91, 8),
        (93, 32),
        (95, 47),
        (360, "0"),
        (92, 5),
        (92, 5),
        (92, -1),
        (92, -1),
        (91, 9),
        (93, 32),
        (95, 48),
        (360, "0"),
        (92, 6),
        (92, 6),
        (92, -1),
        (92, -1),
        (91, 10),
        (93, 32),
        (95, 49),
        (360, "0"),
        (92, -1),
        (92, -1),
        (92, 10),
        (92, 10),
        (91, 11),
        (93, 32),
        (95, 50),
        (360, "0"),
        (92, 8),
        (92, 8),
        (92, -1),
        (92, -1),
        (91, 12),
        (93, 32),
        (95, 51),
        (360, "0"),
        (92, 9),
        (92, 9),
        (92, -1),
        (92, -1),
        (91, 13),
        (93, 32),
        (95, 52),
        (360, "0"),
        (92, 11),
        (92, 11),
        (92, -1),
        (92, -1),
        (92, 0),
        (93, 0),
        (94, 1),
        (91, 3),
        (91, 2),
        (92, -1),
        (92, 4),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, 1),
        (93, 0),
        (94, 1),
        (91, 2),
        (91, 4),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, 2),
        (92, -1),
        (92, 2),
        (93, 0),
        (94, 1),
        (91, 2),
        (91, 5),
        (92, -1),
        (92, -1),
        (92, 1),
        (92, 3),
        (92, -1),
        (92, 3),
        (93, 4),
        (94, 1),
        (91, 2),
        (91, 0),
        (92, -1),
        (92, -1),
        (92, 2),
        (92, -1),
        (92, 4),
        (92, 4),
        (93, 4),
        (94, 1),
        (91, 0),
        (91, 2),
        (92, 0),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, 3),
        (92, 5),
        (93, 0),
        (94, 1),
        (91, 6),
        (91, 8),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, 6),
        (92, -1),
        (92, 6),
        (93, 0),
        (94, 1),
        (91, 6),
        (91, 9),
        (92, -1),
        (92, -1),
        (92, 5),
        (92, 8),
        (92, -1),
        (92, 7),
        (93, 0),
        (94, 2),
        (91, 7),
        (91, 6),
        (92, -1),
        (92, 10),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, 8),
        (93, 0),
        (94, 1),
        (91, 6),
        (91, 11),
        (92, -1),
        (92, -1),
        (92, 6),
        (92, 9),
        (92, -1),
        (92, 9),
        (93, 0),
        (94, 1),
        (91, 6),
        (91, 12),
        (92, -1),
        (92, -1),
        (92, 8),
        (92, 11),
        (92, -1),
        (92, 10),
        (93, 0),
        (94, 2),
        (91, 10),
        (91, 6),
        (92, 7),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, -1),
        (92, 11),
        (93, 0),
        (94, 2),
        (91, 6),
        (91, 13),
        (92, -1),
        (92, -1),
        (92, 9),
        (92, -1),
        (92, -1),
    ]


def set_dynamic_block_properties_table(
    block: BlockLayout,
    table: DynamicBlockPropertiesTable,
) -> DynamicBlockPropertiesTable:
    """Attach a dynamic block properties table to an existing dynamic block.

    This is a minimal authoring helper for the `BLOCKPROPERTIESTABLE` stack
    observed in AutoCAD-authored dynamic blocks. It currently supports string
    table values and expects an existing visibility parameter on `block`.
    """
    doc = block.doc
    if doc is None:
        raise const.DXFStructureError("valid DXF document required")
    _ensure_dynamic_block_properties_appids(doc)
    visibility = get_dynamic_block_visibility_parameter(block)
    if visibility is None:
        raise const.DXFValueError("dynamic block has no visibility parameter")
    linear_parameters = get_dynamic_block_linear_parameters(block)
    stretch_actions = get_dynamic_block_stretch_actions(block)
    if len(linear_parameters) > 1:
        raise const.DXFValueError("multiple dynamic block linear parameters are not supported")
    if len(stretch_actions) != len(linear_parameters):
        raise const.DXFValueError("linear parameter and stretch action counts do not match")

    resolved_columns = _resolve_property_table_columns(block, table, visibility)
    _tag_block_representation_entities(block)
    for index, entity in enumerate(block):
        if entity.dxftype() == "ATTDEF":
            _ensure_property_attdef_metadata(entity, index)
            entity.dxf.discard("invisible")
    _delete_graph_stack(block.block_record)

    true_name = block.name
    if block.block_record.has_xdata(AcDbDynamicBlockTrueName):
        for tag in block.block_record.get_xdata(AcDbDynamicBlockTrueName):
            if tag.code == 1000 and tag.value:
                true_name = str(tag.value)
                break
        block.block_record.discard_xdata(AcDbDynamicBlockTrueName)
    block.block_record.set_xdata(AcDbDynamicBlockTrueName2, [(1000, true_name)])

    xdict = _ensure_dynamic_block_extension_dict(block.block_record)
    graph = _new_tag_storage_object(
        doc,
        "ACAD_EVALUATION_GRAPH",
        xdict.dxf.handle,
        [[
            (100, "AcDbEvalGraph"),
            (96, 35),
            (97, 35),
            (91, 0),
            (93, 32),
            (95, 6),
            (360, "0"),
            (92, 3),
            (92, 3),
            (92, 4),
            (92, 4),
            (91, 1),
            (93, 32),
            (95, 16),
            (360, "0"),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, -1),
            (91, 2),
            (93, 32),
            (95, 32),
            (360, "0"),
            (92, 0),
            (92, 4),
            (92, 1),
            (92, 3),
            (91, 3),
            (93, 32),
            (95, 33),
            (360, "0"),
            (92, -1),
            (92, -1),
            (92, 0),
            (92, 0),
            (91, 4),
            (93, 32),
            (95, 34),
            (360, "0"),
            (92, 1),
            (92, 1),
            (92, -1),
            (92, -1),
            (91, 5),
            (93, 32),
            (95, 35),
            (360, "0"),
            (92, 2),
            (92, 2),
            (92, -1),
            (92, -1),
            (92, 0),
            (93, 0),
            (94, 1),
            (91, 3),
            (91, 2),
            (92, -1),
            (92, 4),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, 1),
            (93, 0),
            (94, 1),
            (91, 2),
            (91, 4),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, 2),
            (92, -1),
            (92, 2),
            (93, 0),
            (94, 1),
            (91, 2),
            (91, 5),
            (92, -1),
            (92, -1),
            (92, 1),
            (92, 3),
            (92, -1),
            (92, 3),
            (93, 4),
            (94, 1),
            (91, 2),
            (91, 0),
            (92, -1),
            (92, -1),
            (92, 2),
            (92, -1),
            (92, 4),
            (92, 4),
            (93, 4),
            (94, 1),
            (91, 0),
            (91, 2),
            (92, 0),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, 3),
        ]],
    )
    _set_owner_reactor(graph, xdict.dxf.handle)
    graph.set_xdata(AcadBPTGraphNodeId, [(1071, 32)])
    xdict.add("ACAD_ENHANCEDBLOCK", graph)
    purge = _new_tag_storage_object(
        doc,
        "ACDB_DYNAMICBLOCKPURGEPREVENTER_VERSION",
        xdict.dxf.handle,
        [[(100, "AcDbDynamicBlockPurgePreventer"), (70, 1)]],
    )
    _set_owner_reactor(purge, xdict.dxf.handle)
    xdict.add("AcDbDynamicBlockRoundTripPurgePreventer", purge)

    proxy = _new_tag_storage_object(
        doc,
        "ACDB_DYNAMICBLOCKPROXYNODE",
        graph.dxf.handle,
        [[(100, "AcDbEvalExpr"), (90, 16), (98, 33), (99, 378)]],
    )
    grip = _new_tag_storage_object(
        doc,
        "BLOCKPROPERTIESTABLEGRIP",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 33), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, "Grip"), (98, 33), (99, 378), (1071, 0)],
            [
                (100, "AcDbBlockGrip"),
                (91, 34),
                (92, 35),
                (1010, table.grip_location or table.location),
                (280, 0),
                (93, -1),
            ],
        ],
    )
    x_comp = _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 34), (98, 33), (99, 378), (1, ""), (70, 40), (140, 0.0)],
            [(100, "AcDbBlockGripExpr"), (91, 32), (300, "UpdatedX")],
        ],
    )
    y_comp = _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 35), (98, 33), (99, 378), (1, ""), (70, 40), (140, 0.0)],
            [(100, "AcDbBlockGripExpr"), (91, 32), (300, "UpdatedY")],
        ],
    )
    visibility_entity = _new_tag_storage_object(
        doc,
        "BLOCKVISIBILITYPARAMETER",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 6), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, visibility.label), (98, 33), (99, 378), (1071, 0)],
            [(100, "AcDbBlockParameter"), (280, 1), (281, 0)],
            [(100, "AcDbBlock1PtParameter"), (1010, visibility.location), (93, 0), (170, 0), (171, 0)],
            _build_property_visibility_parameter_subclass(visibility, "0", grip.dxf.handle),
        ],
    )
    table_entity = _new_tag_storage_object(
        doc,
        "BLOCKPROPERTIESTABLE",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 32), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, table.label), (98, 33), (99, 378), (1071, 0)],
            [(100, "AcDbBlockParameter"), (280, 1), (281, 0)],
            [(100, "AcDbBlock1PtParameter"), (1010, table.location), (93, 33), (170, 0), (171, 0)],
            _build_block_properties_table_subclass(table, [
                *resolved_columns[:-1],
                DynamicBlockPropertyColumn(
                    source_handle=visibility_entity.dxf.handle,
                    source_dxftype="BLOCKVISIBILITYPARAMETER",
                    name=resolved_columns[-1].name,
                    display_name=resolved_columns[-1].display_name,
                ),
            ]),
        ],
    )
    _set_property_attdef_reactors(block, table_entity.dxf.handle)

    # Patch the visibility parameter with the actual table handle once it exists.
    vis_subclass = visibility_entity.xtags.get_subclass("AcDbBlockVisibilityParameter")
    patched_tags = _build_property_visibility_parameter_subclass(
        visibility,
        table_entity.dxf.handle,
        grip.dxf.handle,
    )
    _replace_subclass_tags(vis_subclass, patched_tags)
    visibility_entity.set_reactors([table_entity.dxf.handle])

    handles = [
        visibility_entity.dxf.handle,
        proxy.dxf.handle,
        table_entity.dxf.handle,
        grip.dxf.handle,
        x_comp.dxf.handle,
        y_comp.dxf.handle,
    ]
    _patch_eval_graph_handles(graph, handles)

    if linear_parameters:
        set_dynamic_block_linear_parameter(block, linear_parameters[0], stretch_actions[0])

    return DynamicBlockPropertiesTable(
        handle=table_entity.dxf.handle or "",
        label=table.label,
        table_name=table.table_name,
        description=table.description,
        location=table.location,
        grip_location=table.grip_location,
        columns=tuple([
            *resolved_columns[:-1],
            DynamicBlockPropertyColumn(
                source_handle=visibility_entity.dxf.handle or "",
                source_dxftype="BLOCKVISIBILITYPARAMETER",
                name=resolved_columns[-1].name,
                display_name=resolved_columns[-1].display_name,
            ),
        ]),
        rows=table.rows,
    )


def set_dynamic_block_linear_parameter(
    block: BlockLayout,
    parameter: DynamicBlockLinearParameter,
    stretch_action: DynamicBlockStretchAction,
) -> DynamicBlockLinearParameter:
    doc = block.doc
    if doc is None:
        raise const.DXFStructureError("valid DXF document required")
    if get_dynamic_block_linear_parameters(block):
        raise const.DXFValueError("multiple dynamic block linear parameters are not supported")
    visibility = get_dynamic_block_visibility_parameter(block)
    properties = get_dynamic_block_properties_table(block)
    if visibility is None or properties is None:
        raise const.DXFValueError("dynamic block requires visibility and properties table")
    graph = _get_enhanced_block_graph(block.block_record)
    if graph is None:
        raise const.DXFStructureError("dynamic block graph not found")

    owned = tuple(_iter_graph_owned_objects(graph))
    visibility_entity = next((entity for entity in owned if entity.dxftype() == "BLOCKVISIBILITYPARAMETER"), None)
    table_entity = next((entity for entity in owned if entity.dxftype() == "BLOCKPROPERTIESTABLE"), None)
    proxy = next((entity for entity in owned if entity.dxftype() == "ACDB_DYNAMICBLOCKPROXYNODE"), None)
    table_grip = next((entity for entity in owned if entity.dxftype() == "BLOCKPROPERTIESTABLEGRIP"), None)
    property_components = [entity for entity in owned if entity.dxftype() == "BLOCKGRIPLOCATIONCOMPONENT"]
    if not isinstance(visibility_entity, DXFTagStorage):
        raise const.DXFStructureError("visibility parameter object not found")
    if not isinstance(table_entity, DXFTagStorage):
        raise const.DXFStructureError("properties table object not found")
    if not isinstance(proxy, DXFTagStorage):
        raise const.DXFStructureError("dynamic block proxy node not found")
    if not isinstance(table_grip, DXFTagStorage):
        raise const.DXFStructureError("properties table grip not found")
    if len(property_components) != 2:
        raise const.DXFStructureError("properties table grip components not found")

    x_comp = next((entity for entity in property_components if entity.xtags.get_subclass("AcDbBlockGripExpr").get_first_value(300, "") == "UpdatedX"), None)
    y_comp = next((entity for entity in property_components if entity.xtags.get_subclass("AcDbBlockGripExpr").get_first_value(300, "") == "UpdatedY"), None)
    if not isinstance(x_comp, DXFTagStorage) or not isinstance(y_comp, DXFTagStorage):
        raise const.DXFStructureError("properties table grip components not found")

    source_attdefs = _get_property_attdefs(block)
    linear_visibility = _augment_visibility_with_property_attdefs(visibility, source_attdefs)
    primary_entity_handle = next(
        (entity.dxf.handle for entity in block if entity.dxftype() != "ATTDEF" and entity.dxf.handle),
        "",
    )
    dependency_handles = stretch_action.dependency_handles or tuple(
        handle
        for handle in (
            table_grip.dxf.handle,
            table_entity.dxf.handle,
            *[attdef.dxf.handle for attdef in reversed(source_attdefs)],
            primary_entity_handle,
        )
        if handle
    )
    targets = stretch_action.targets or tuple(
        [
            *(
                [DynamicBlockStretchActionTarget(primary_entity_handle, 2, (1, 2))]
                if primary_entity_handle
                else []
            ),
            *[
                DynamicBlockStretchActionTarget(attdef.dxf.handle, 1, (0,))
                for attdef in source_attdefs
                if attdef.dxf.handle
            ],
        ]
    )
    vector = (
        float(parameter.end_point[0] - parameter.base_point[0]),
        float(parameter.end_point[1] - parameter.base_point[1]),
        float(parameter.end_point[2] - parameter.base_point[2]),
    )
    base_grip_label = parameter.base_grip_label or "Base Grip"
    end_grip_label = parameter.end_grip_label or "End Grip"

    linear_entity = _new_tag_storage_object(
        doc,
        "BLOCKLINEARPARAMETER",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 45), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, parameter.label), (98, 33), (99, 378), (1071, 32)],
            [(100, "AcDbBlockParameter"), (280, 1), (281, 0)],
            [
                (100, "AcDbBlock2PtParameter"),
                (1010, parameter.base_point),
                (1011, parameter.end_point),
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
                (305, parameter.parameter_name),
                (306, parameter.description),
                (140, parameter.distance),
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
            [(100, "AcDbBlockElement"), (300, end_grip_label), (98, 33), (99, 378), (1071, 0)],
            [(100, "AcDbBlockGrip"), (91, 47), (92, 48), (1010, parameter.end_point), (280, 1), (93, -1)],
            [(100, "AcDbBlockLinearGrip"), (140, vector[0]), (141, vector[1]), (142, vector[2])],
        ],
    )
    end_x = _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 47), (98, 33), (99, 378), (1, ""), (70, 40), (140, 1.797693134862314e+99)],
            [(100, "AcDbBlockGripExpr"), (91, 45), (300, "UpdatedEndX")],
        ],
    )
    end_y = _new_tag_storage_object(
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
            [(100, "AcDbBlockElement"), (300, base_grip_label), (98, 33), (99, 378), (1071, 0)],
            [(100, "AcDbBlockGrip"), (91, 50), (92, 51), (1010, parameter.base_point), (280, 1), (93, -1)],
            [(100, "AcDbBlockLinearGrip"), (140, -vector[0]), (141, -vector[1]), (142, -vector[2])],
        ],
    )
    base_x = _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 50), (98, 33), (99, 378), (1, ""), (70, 40), (140, 0.0)],
            [(100, "AcDbBlockGripExpr"), (91, 45), (300, "UpdatedBaseX")],
        ],
    )
    base_y = _new_tag_storage_object(
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
            [(100, "AcDbBlockElement"), (300, stretch_action.label), (98, 33), (99, 378), (1071, 0)],
            [
                (100, "AcDbBlockAction"),
                (70, 1),
                (91, 32),
                (71, len(dependency_handles)),
                *[(330, handle) for handle in dependency_handles],
                (1010, stretch_action.action_location),
            ],
            [
                (100, "AcDbBlockStretchAction"),
                (92, 45),
                (301, stretch_action.x_name or "EndXDelta"),
                (93, 45),
                (302, stretch_action.y_name or "EndYDelta"),
                (72, len(stretch_action.selection_window)),
                *[(1011, point) for point in stretch_action.selection_window],
                (73, len(targets)),
                *[
                    tag
                    for target in targets
                    for tag in (
                        (331, target.entity_handle),
                        (74, target.mode),
                        *[(94, component) for component in target.components],
                    )
                ],
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

    vis_subclass = visibility_entity.xtags.get_subclass("AcDbBlockVisibilityParameter")
    _replace_subclass_tags(
        vis_subclass,
        _build_property_visibility_parameter_subclass(
            linear_visibility,
            table_entity.dxf.handle,
            table_grip.dxf.handle,
            extra_state_refs=((base_grip.dxf.handle, linear_entity.dxf.handle, end_grip.dxf.handle, stretch.dxf.handle), (), ()),
            all_handles=linear_visibility.all_entity_handles,
        ),
    )
    _replace_subclass_tags(graph.xtags.get_subclass("AcDbEvalGraph"), _build_linear_eval_graph_subclass())
    _patch_eval_graph_handles(
        graph,
        [
            visibility_entity.dxf.handle,
            proxy.dxf.handle,
            table_entity.dxf.handle,
            table_grip.dxf.handle,
            x_comp.dxf.handle,
            y_comp.dxf.handle,
            linear_entity.dxf.handle,
            end_grip.dxf.handle,
            end_x.dxf.handle,
            end_y.dxf.handle,
            base_grip.dxf.handle,
            base_x.dxf.handle,
            base_y.dxf.handle,
            stretch.dxf.handle,
        ],
    )
    return DynamicBlockLinearParameter(
        handle=linear_entity.dxf.handle or "",
        label=parameter.label,
        parameter_name=parameter.parameter_name,
        description=parameter.description,
        base_point=parameter.base_point,
        end_point=parameter.end_point,
        distance=parameter.distance,
        expr_id=45,
        base_grip_handle=base_grip.dxf.handle or "",
        end_grip_handle=end_grip.dxf.handle or "",
        base_grip_label=base_grip_label,
        end_grip_label=end_grip_label,
    )


def set_dynamic_block_properties_editor_support(
    block: BlockLayout,
    table: DynamicBlockPropertiesTable,
) -> tuple[DynamicBlockPropertyRepresentation, ...]:
    """Create a first-pass editor-support layer for dynamic block properties.

    This helper authors hidden property representation blocks and assoc-network
    bundles derived from the authored table rows. The structure is intentionally
    simpler than the full AutoCAD-normalized graph, but preserves the important
    patterns we observed in the golden file.
    """
    doc = block.doc
    if doc is None:
        raise const.DXFStructureError("valid DXF document required")
    visibility = get_dynamic_block_visibility_parameter(block)
    properties = get_dynamic_block_properties_table(block)
    if visibility is None or properties is None:
        raise const.DXFValueError("dynamic block requires visibility and properties table")

    _delete_hidden_dynamic_support_blocks(block.block_record)
    root_network = _ensure_root_assoc_network(doc)
    created: list[DynamicBlockPropertyRepresentation] = []
    child_networks: list[str] = []
    source_attdefs = _get_property_attdefs(block)
    visible_state_name = visibility.states[0].name if visibility.states else ""
    state_names = [state.name for state in visibility.states]
    linear_parameters = get_dynamic_block_linear_parameters(block)

    def add_hidden_representation(
        *,
        state_name: str | None,
        carrier_count: int,
        carrier_text: str,
        carriers_visible: bool,
        assoc_values: Sequence[tuple[str, str]] = (),
        carrier_metadata_indices: Optional[Sequence[int]] = None,
        carrier_reactor_indices: Optional[Sequence[int]] = None,
    ) -> None:
        hidden = doc.blocks.new_anonymous_block(type_char="U")
        if state_name is None:
            clone_geometry_visible(hidden)
        else:
            clone_geometry_and_masks(hidden, state_name)
        set_dynamic_block_reference(hidden, block, clone_property_attdefs=False)
        for attdef in source_attdefs[:carrier_count]:
            _clone_property_attdef(
                attdef,
                hidden,
                text=carrier_text,
                invisible=not carriers_visible,
            )
        _tag_block_representation_entities(hidden)
        carrier_items: list[tuple[int, Any, int]] = []
        for index, entity in enumerate(hidden):
            if entity.dxftype() == "ATTDEF":
                _set_property_attdef_rep_etag(entity, index)
                carrier_items.append((len(carrier_items), entity, index))
        metadata_indices = (
            {carrier_index for carrier_index, _, _ in carrier_items}
            if carrier_metadata_indices is None
            else set(carrier_metadata_indices)
        )
        reactor_indices = (
            {carrier_index for carrier_index, _, _ in carrier_items}
            if carrier_reactor_indices is None
            else set(carrier_reactor_indices)
        )
        for carrier_index, entity, hidden_index in carrier_items:
            if carrier_index in metadata_indices:
                _ensure_property_attdef_annotative_metadata(entity)
            if carrier_index in reactor_indices:
                entity.set_reactors([properties.handle])
        assoc_network = None
        if assoc_values:
            assoc_network = _new_assoc_network_bundle(
                hidden.block_record,
                root_network.dxf.handle,
                assoc_values,
                action_index=len(child_networks) + 1,
            )
            child_networks.append(assoc_network.handle)
        carriers = tuple(
            DynamicBlockPropertyCarrier(
                handle=entity.dxf.handle or "",
                tag=entity.dxf.tag,
                text=entity.dxf.text,
                invisible=int(entity.dxf.get("invisible", 0)),
            )
            for entity in hidden
            if entity.dxftype() == "ATTDEF"
        )
        created.append(
            DynamicBlockPropertyRepresentation(
                block_record_handle=hidden.block_record.dxf.handle or "",
                block_name=hidden.name,
                is_active=False,
                invisible_flags=tuple(int(entity.dxf.get("invisible", 0)) for entity in hidden),
                carriers=carriers,
                assoc_network=assoc_network,
            )
        )

    def clone_geometry_and_masks(target: BlockLayout, state_name: str) -> None:
        _clone_non_attdef_entities(block, target)
        _tag_block_representation_entities(target)
        _apply_visibility_state_to_block(target, visibility, state_name, dynamic_block=block)

    def clone_geometry_visible(target: BlockLayout) -> None:
        _clone_non_attdef_entities(block, target)
        _tag_block_representation_entities(target)
        for entity in target:
            entity.dxf.discard("invisible")

    def use_golden_style_templates() -> bool:
        return (
            len(source_attdefs) == 3
            and len(properties.columns) == 4
            and len(properties.rows) == 27
            and len(state_names) == 3
        )

    def use_linear_golden_style_templates() -> bool:
        return use_golden_style_templates() and len(linear_parameters) == 1

    if use_linear_golden_style_templates():
        pair = (0, 1)
        triple_heads = (0, 1)
        triple_all = (0, 1, 2)

        for _ in range(2):
            add_hidden_representation(state_name=None, carrier_count=0, carrier_text="", carriers_visible=True)
        for state_name in state_names:
            add_hidden_representation(state_name=state_name, carrier_count=0, carrier_text="", carriers_visible=True)

        for _ in range(8):
            add_hidden_representation(
                state_name=visible_state_name,
                carrier_count=2,
                carrier_text="",
                carriers_visible=True,
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )
        for _ in range(25):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )
        for _ in range(23):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )

        for _ in range(1):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=3,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(3):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=3,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )

        for _ in range(1):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=3,
                carrier_text="Block Table 1",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(2):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=3,
                carrier_text="Block Table 1",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )

        for _ in range(5):
            add_hidden_representation(
                state_name=visible_state_name,
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=True,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(1):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=True,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(1):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=True,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(8):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=False,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(6):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=False,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )

        _set_root_assoc_children(root_network, child_networks)
        return tuple(created)

    if use_golden_style_templates():
        pair = (0, 1)
        pair_first = (0,)
        pair_second = (1,)
        triple_heads = (0, 1)
        triple_all = (0, 1, 2)

        # Visibility-only support blocks: 2 fully visible + one masked rep per state.
        for _ in range(2):
            add_hidden_representation(state_name=None, carrier_count=0, carrier_text="", carriers_visible=True)
        for state_name in state_names:
            add_hidden_representation(state_name=state_name, carrier_count=0, carrier_text="", carriers_visible=True)

        # 2-carrier editor support families, matched to the golden file counts.
        for _ in range(5):
            add_hidden_representation(
                state_name=visible_state_name,
                carrier_count=2,
                carrier_text="",
                carriers_visible=True,
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )
        add_hidden_representation(
            state_name=visible_state_name,
            carrier_count=2,
            carrier_text="",
            carriers_visible=True,
            carrier_metadata_indices=(),
            carrier_reactor_indices=pair_first,
        )
        for _ in range(9):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )
        add_hidden_representation(
            state_name=state_names[1],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            carrier_metadata_indices=(),
            carrier_reactor_indices=pair_first,
        )
        for _ in range(2):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair_second,
            )
        for _ in range(5):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=pair,
                carrier_reactor_indices=pair,
            )
        for _ in range(10):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )
        add_hidden_representation(
            state_name=state_names[2],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            carrier_metadata_indices=(),
            carrier_reactor_indices=pair_first,
        )
        add_hidden_representation(
            state_name=state_names[2],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            carrier_metadata_indices=(),
            carrier_reactor_indices=pair_second,
        )
        for _ in range(5):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=pair,
                carrier_reactor_indices=pair,
            )

        add_hidden_representation(
            state_name=visible_state_name,
            carrier_count=2,
            carrier_text="",
            carriers_visible=True,
            assoc_values=(("user1", "1"),),
            carrier_metadata_indices=(),
            carrier_reactor_indices=pair,
        )
        add_hidden_representation(
            state_name=state_names[1],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            assoc_values=(("user1", "1"),),
            carrier_metadata_indices=(),
            carrier_reactor_indices=pair,
        )
        add_hidden_representation(
            state_name=state_names[2],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            assoc_values=(("user1", "1"),),
            carrier_metadata_indices=(),
            carrier_reactor_indices=pair,
        )

        add_hidden_representation(
            state_name=visible_state_name,
            carrier_count=2,
            carrier_text="",
            carriers_visible=True,
            assoc_values=(("user1", "1"), ("user2", "1")),
            carrier_metadata_indices=(),
            carrier_reactor_indices=(),
        )
        add_hidden_representation(
            state_name=state_names[1],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            assoc_values=(("user1", "1"), ("user2", "1")),
            carrier_metadata_indices=(),
            carrier_reactor_indices=(),
        )
        for _ in range(4):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                assoc_values=(("user1", "1"), ("user2", "1")),
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )
        for _ in range(2):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                assoc_values=(("user1", "1"), ("user2", "1")),
                carrier_metadata_indices=pair,
                carrier_reactor_indices=pair,
            )
        add_hidden_representation(
            state_name=state_names[2],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            assoc_values=(("user1", "1"), ("user2", "1")),
            carrier_metadata_indices=(),
            carrier_reactor_indices=(),
        )
        for _ in range(2):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=2,
                carrier_text="",
                carriers_visible=False,
                assoc_values=(("user1", "1"), ("user2", "1")),
                carrier_metadata_indices=(),
                carrier_reactor_indices=pair,
            )
        add_hidden_representation(
            state_name=state_names[2],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            assoc_values=(("user1", "1"), ("user2", "1")),
            carrier_metadata_indices=pair,
            carrier_reactor_indices=pair,
        )
        add_hidden_representation(
            state_name=state_names[2],
            carrier_count=2,
            carrier_text="",
            carriers_visible=False,
            assoc_values=(("user1", "5667"), ("user2", "8")),
            carrier_metadata_indices=(),
            carrier_reactor_indices=(),
        )

        # 3-carrier support families.
        for _ in range(1):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=3,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(3):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=3,
                carrier_text="",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )

        for _ in range(1):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=3,
                carrier_text="Block Table 1",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(2):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=3,
                carrier_text="Block Table 1",
                carriers_visible=False,
                carrier_metadata_indices=triple_heads,
                carrier_reactor_indices=triple_all,
            )

        for _ in range(3):
            add_hidden_representation(
                state_name=visible_state_name,
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=True,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(7):
            add_hidden_representation(
                state_name=state_names[1],
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=False,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )
        for _ in range(5):
            add_hidden_representation(
                state_name=state_names[2],
                carrier_count=3,
                carrier_text=properties.table_name,
                carriers_visible=False,
                carrier_metadata_indices=triple_all,
                carrier_reactor_indices=triple_all,
            )

        _set_root_assoc_children(root_network, child_networks)
        return tuple(created)

    # Hidden visibility-only support blocks observed in AutoCAD-authored files:
    # two fully visible generic reps and one masked rep for each visibility state.
    for _ in range(2):
        generic = doc.blocks.new_anonymous_block(type_char="U")
        clone_geometry_visible(generic)
        set_dynamic_block_reference(generic, block, clone_property_attdefs=False)
    for visibility_state in visibility.states:
        hidden = doc.blocks.new_anonymous_block(type_char="U")
        clone_geometry_and_masks(hidden, visibility_state.name)
        set_dynamic_block_reference(hidden, block, clone_property_attdefs=False)

    # Hidden 2-column prefix representations keyed by the first 2 properties.
    for row in properties.rows:
        prefix_values = tuple(str(value) for value in row.values[:2])
        state_name = str(row.values[-1])
        hidden = doc.blocks.new_anonymous_block(type_char="U")
        clone_geometry_and_masks(hidden, state_name)
        set_dynamic_block_reference(hidden, block, clone_property_attdefs=False)
        for attdef in source_attdefs[:2]:
            _clone_property_attdef(attdef, hidden, text="", invisible=state_name != visible_state_name)
        _tag_block_representation_entities(hidden)
        for index, entity in enumerate(hidden):
            if entity.dxftype() == "ATTDEF":
                _ensure_property_attdef_metadata(entity, index)
        _set_property_attdef_reactors(hidden, properties.handle)
        network = _new_assoc_network_bundle(
            hidden.block_record,
            root_network.dxf.handle,
            (("user1", prefix_values[0]), ("user2", prefix_values[1])),
            action_index=row.index + 1,
        )
        child_networks.append(network.handle)
        carriers = tuple(
            DynamicBlockPropertyCarrier(
                handle=entity.dxf.handle or "",
                tag=entity.dxf.tag,
                text=entity.dxf.text,
                invisible=int(entity.dxf.get("invisible", 0)),
            )
            for entity in hidden
            if entity.dxftype() == "ATTDEF"
        )
        created.append(
            DynamicBlockPropertyRepresentation(
                block_record_handle=hidden.block_record.dxf.handle or "",
                block_name=hidden.name,
                is_active=False,
                invisible_flags=tuple(int(entity.dxf.get("invisible", 0)) for entity in hidden),
                carriers=carriers,
                assoc_network=network,
            )
        )

    # Hidden full 3-column row representations.
    for row in properties.rows:
        state_name = str(row.values[-1])
        hidden = doc.blocks.new_anonymous_block(type_char="U")
        clone_geometry_and_masks(hidden, state_name)
        set_dynamic_block_reference(hidden, block, clone_property_attdefs=False)
        for attdef, value in zip(source_attdefs, row.values[: len(source_attdefs)]):
            _clone_property_attdef(
                attdef,
                hidden,
                text=properties.table_name,
                invisible=state_name != visible_state_name,
            )
        _tag_block_representation_entities(hidden)
        for index, entity in enumerate(hidden):
            if entity.dxftype() == "ATTDEF":
                _ensure_property_attdef_metadata(entity, index)
        _set_property_attdef_reactors(hidden, properties.handle)
        carriers = tuple(
            DynamicBlockPropertyCarrier(
                handle=entity.dxf.handle or "",
                tag=entity.dxf.tag,
                text=entity.dxf.text,
                invisible=int(entity.dxf.get("invisible", 0)),
            )
            for entity in hidden
            if entity.dxftype() == "ATTDEF"
        )
        created.append(
            DynamicBlockPropertyRepresentation(
                block_record_handle=hidden.block_record.dxf.handle or "",
                block_name=hidden.name,
                is_active=False,
                invisible_flags=tuple(int(entity.dxf.get("invisible", 0)) for entity in hidden),
                carriers=carriers,
                assoc_network=None,
            )
        )

    _set_root_assoc_children(root_network, child_networks)
    return tuple(created)


def _new_tag_storage_object(doc: Drawing, dxftype: str, owner: str, subclasses) -> DXFTagStorage:
    from ezdxf.entities import factory
    from ezdxf.lldxf.extendedtags import ExtendedTags
    from ezdxf.lldxf.types import dxftag

    entity = factory.new(dxftype, dxfattribs={"owner": owner}, doc=doc)
    factory.bind(entity, doc)
    doc.objects.add_object(entity)
    tags = [
        dxftag(0, dxftype),
        dxftag(5, entity.dxf.handle),
        dxftag(330, owner),
    ]
    for subclass in subclasses:
        tags.extend(dxftag(code, value) for code, value in subclass)
    xtags = ExtendedTags(tags)
    entity.load_tags(xtags, dxfversion=doc.dxfversion)
    entity.store_tags(xtags)
    return entity


def _set_owner_reactor(entity: DXFTagStorage, owner: str) -> None:
    entity.set_reactors([owner])


def _ensure_dynamic_block_extension_dict(block_record: BlockRecord) -> Dictionary:
    xdict = block_record.get_extension_dict() if block_record.has_extension_dict else block_record.new_extension_dict()
    return xdict.dictionary


def set_dynamic_block_visibility_parameter(
    block: BlockLayout,
    parameter: DynamicBlockVisibilityParameter,
    *,
    guid: str = "",
    true_name: str = "",
) -> None:
    """Attach a minimal visibility-state dynamic-block graph to `block`.

    This helper models the visibility parameter stack observed in AutoCAD-authored
    dynamic blocks. It is intentionally minimal and currently limited to the
    visibility-parameter feature set.
    """
    doc = block.doc
    if doc is None:
        raise const.DXFStructureError("valid DXF document required")
    _ensure_dynamic_block_appids(doc)
    block_record = block.block_record
    if not guid:
        guid = "{" + str(uuid.uuid4()).upper() + "}"
    if not true_name:
        true_name = block.name
    block_record.set_xdata(AcDbDynamicBlockGUID, [(1000, guid)])
    block_record.set_xdata(AcDbDynamicBlockTrueName, [(1000, true_name)])
    block_record.set_xdata(AcDbBlockRepETag, [(1070, 1), (1071, len(block))])
    _tag_block_representation_entities(block)
    if len(parameter.states):
        _apply_visibility_state_to_block(block, parameter, parameter.states[0].name)

    xdict = _ensure_dynamic_block_extension_dict(block_record)
    graph = _new_tag_storage_object(
        doc,
        "ACAD_EVALUATION_GRAPH",
        xdict.dxf.handle,
        [[
            (100, "AcDbEvalGraph"),
            (96, 9),
            (97, 9),
            (91, 0),
            (93, 32),
            (95, 6),
            (360, "0"),
            (92, 0),
            (92, 0),
            (92, 1),
            (92, 2),
            (91, 1),
            (93, 32),
            (95, 7),
            (360, "0"),
            (92, -1),
            (92, -1),
            (92, 0),
            (92, 0),
            (91, 2),
            (93, 32),
            (95, 8),
            (360, "0"),
            (92, 1),
            (92, 1),
            (92, -1),
            (92, -1),
            (91, 3),
            (93, 32),
            (95, 9),
            (360, "0"),
            (92, 2),
            (92, 2),
            (92, -1),
            (92, -1),
            (92, 0),
            (93, 0),
            (94, 1),
            (91, 1),
            (91, 0),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, 1),
            (93, 0),
            (94, 1),
            (91, 0),
            (91, 2),
            (92, -1),
            (92, -1),
            (92, -1),
            (92, 2),
            (92, -1),
            (92, 2),
            (93, 0),
            (94, 1),
            (91, 0),
            (91, 3),
            (92, -1),
            (92, -1),
            (92, 1),
            (92, -1),
            (92, -1),
        ]],
    )
    _set_owner_reactor(graph, xdict.dxf.handle)
    xdict.add("ACAD_ENHANCEDBLOCK", graph)
    purge = _new_tag_storage_object(
        doc,
        "ACDB_DYNAMICBLOCKPURGEPREVENTER_VERSION",
        xdict.dxf.handle,
        [[(100, "AcDbDynamicBlockPurgePreventer"), (70, 1)]],
    )
    _set_owner_reactor(purge, xdict.dxf.handle)
    xdict.add("AcDbDynamicBlockRoundTripPurgePreventer", purge)

    ordered_handles = list(parameter.all_entity_handles)
    if not ordered_handles:
        for state in parameter.states:
            for handle in state.entity_handles:
                if handle not in ordered_handles:
                    ordered_handles.append(handle)

    vis_subclass = [
        (100, "AcDbBlockVisibilityParameter"),
        (281, 1),
        (301, parameter.parameter_name),
        (302, ""),
        (91, 0),
        (93, len(ordered_handles)),
        *[(331, handle) for handle in ordered_handles],
        (92, len(parameter.states)),
    ]
    for state in parameter.states:
        vis_subclass.extend(
            [
                (303, state.name),
                (94, len(state.entity_handles)),
                *[(332, handle) for handle in state.entity_handles],
                (95, 0),
            ]
        )

    px, py, pz = parameter.location
    visibility = _new_tag_storage_object(
        doc,
        "BLOCKVISIBILITYPARAMETER",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 6), (98, 33), (99, 378)],
            [
                (100, "AcDbBlockElement"),
                (300, parameter.label),
                (98, 33),
                (99, 378),
                (1071, 0),
            ],
            [(100, "AcDbBlockParameter"), (280, 1), (281, 0)],
            [
                (100, "AcDbBlock1PtParameter"),
                (1010, (px, py, pz)),
                (93, 7),
                (170, 0),
                (171, 0),
            ],
            vis_subclass,
        ],
    )

    grip = _new_tag_storage_object(
        doc,
        "BLOCKVISIBILITYGRIP",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 7), (98, 33), (99, 378)],
            [(100, "AcDbBlockElement"), (300, "Grip"), (98, 33), (99, 378), (1071, 0)],
            [
                (100, "AcDbBlockGrip"),
                (91, 8),
                (92, 9),
                (1010, (px, py, pz)),
                (280, 0),
                (93, -1),
            ],
            [(100, "AcDbBlockVisibilityGrip")],
        ],
    )
    updated_x = _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 8), (98, 33), (99, 378), (1, ""), (70, 40), (140, 0.0)],
            [(100, "AcDbBlockGripExpr"), (91, 6), (300, "UpdatedX")],
        ],
    )
    updated_y = _new_tag_storage_object(
        doc,
        "BLOCKGRIPLOCATIONCOMPONENT",
        graph.dxf.handle,
        [
            [(100, "AcDbEvalExpr"), (90, 9), (98, 33), (99, 378), (1, ""), (70, 40), (140, 0.0)],
            [(100, "AcDbBlockGripExpr"), (91, 6), (300, "UpdatedY")],
        ],
    )

    eval_graph = graph.xtags.get_subclass("AcDbEvalGraph")
    handles = [
        visibility.dxf.handle,
        grip.dxf.handle,
        updated_x.dxf.handle,
        updated_y.dxf.handle,
    ]
    from ezdxf.lldxf.types import dxftag

    handle_index = 0
    for index, tag in enumerate(eval_graph):
        if tag.code == 360 and handle_index < len(handles):
            eval_graph[index] = dxftag(360, handles[handle_index])
            handle_index += 1


def set_dynamic_block_reference(
    block: BlockLayout,
    dynamic_block: BlockLayout,
    *,
    clone_property_attdefs: bool = True,
) -> None:
    """Mark `block` as an anonymous representation of `dynamic_block`."""
    if block.doc is None:
        raise const.DXFStructureError("valid DXF document required")
    _ensure_dynamic_block_appids(block.doc)
    if not block.block_record.has_extension_dict:
        block.block_record.new_extension_dict()
    if clone_property_attdefs:
        _clone_property_attdefs_to_reference(block, dynamic_block)
    _tag_block_representation_entities(block)
    for index, entity in enumerate(block):
        if entity.dxftype() == "ATTDEF":
            _ensure_property_attdef_metadata(entity, index)
    properties = get_dynamic_block_properties_table(dynamic_block)
    if properties is not None:
        _set_property_attdef_reactors(block, properties.handle)
    block.block_record.set_xdata(
        AcDbBlockRepBTag,
        [(1070, 1), (1005, dynamic_block.block_record_handle)],
    )


def set_dynamic_block_visibility_state(
    insert: Insert,
    dynamic_block: Optional[BlockLayout] = None,
    *,
    state: str,
    location: Optional[tuple[float, float, float]] = None,
) -> None:
    """Attach the current visibility-state cache to a dynamic block insert."""
    if dynamic_block is None:
        dynamic_block = get_dynamic_block_definition(insert)
    if dynamic_block is None:
        raise const.DXFStructureError("dynamic block definition not found")
    if insert.doc is None:
        raise const.DXFStructureError("valid DXF document required")
    parameter = get_dynamic_block_visibility_parameter(dynamic_block)
    if parameter is None:
        raise const.DXFValueError("dynamic block has no visibility parameter")
    if location is None:
        location = parameter.location
    reference = get_dynamic_block_reference(insert)
    if reference is not None:
        if not reference.block_record.has_extension_dict:
            reference.block_record.new_extension_dict()
        reference.block_record.blkref_handles = [insert.dxf.handle]
        _apply_visibility_state_to_block(
            reference,
            parameter,
            state,
            dynamic_block=dynamic_block,
        )
        if len(parameter.states):
            _apply_property_attdef_visibility(
                reference,
                dynamic_block,
                state,
                parameter.states[0].name,
            )
    xdict = insert.get_extension_dict() if insert.has_extension_dict else insert.new_extension_dict()
    root = xdict.dictionary
    rep = root.get("AcDbBlockRepresentation")
    if not isinstance(rep, Dictionary):
        rep = root.add_new_dict("AcDbBlockRepresentation", hard_owned=True)
    repdata = rep.get("AcDbRepData")
    if not isinstance(repdata, DXFTagStorage) or repdata.dxftype() != "ACDB_BLOCKREPRESENTATION_DATA":
        repdata = _new_tag_storage_object(
            dynamic_block.doc,
            "ACDB_BLOCKREPRESENTATION_DATA",
            rep.dxf.handle,
            [[(100, "AcDbBlockRepresentationData"), (70, 1), (340, dynamic_block.block_record_handle)]],
        )
        rep.add("AcDbRepData", repdata)
    app_cache = rep.get("AppDataCache")
    if not isinstance(app_cache, Dictionary):
        app_cache = rep.add_new_dict("AppDataCache", hard_owned=True)
    enhanced = app_cache.get("ACAD_ENHANCEDBLOCKDATA")
    if not isinstance(enhanced, Dictionary):
        enhanced = app_cache.add_new_dict("ACAD_ENHANCEDBLOCKDATA", hard_owned=True)
    enhanced.set_reactors([app_cache.dxf.handle])
    xrecord = enhanced.get("6")
    if not isinstance(xrecord, XRecord):
        xrecord = enhanced.add_xrecord("6")
    xrecord.set_reactors([enhanced.dxf.handle])
    xrecord.reset(
        [
            (1071, 135625452),
            (1071, 184556386),
            (70, 25),
            (70, 104),
            (10, location),
            (1, state),
        ]
    )
