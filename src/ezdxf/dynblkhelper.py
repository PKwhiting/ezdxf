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
    "DynamicBlockPropertyColumn",
    "DynamicBlockPropertyRow",
    "DynamicBlockPropertiesTable",
    "get_dynamic_block_definition",
    "get_dynamic_block_reference",
    "is_dynamic_block_definition",
    "get_dynamic_block_record_handle",
    "get_dynamic_block_visibility_parameter",
    "get_dynamic_block_visibility_states",
    "get_dynamic_block_visibility_state",
    "get_dynamic_block_visibility_state_handles",
    "get_dynamic_block_visibility_entities",
    "get_dynamic_block_properties_table",
    "get_dynamic_block_property_columns",
    "get_dynamic_block_property_rows",
    "set_dynamic_block_properties_table",
    "set_dynamic_block_visibility_parameter",
    "set_dynamic_block_reference",
    "set_dynamic_block_visibility_state",
]

AcDbDynamicBlockGUID = "AcDbDynamicBlockGUID"
AcDbBlockRepBTag = "AcDbBlockRepBTag"
AcDbDynamicBlockTrueName = "AcDbDynamicBlockTrueName"
AcDbBlockRepETag = "AcDbBlockRepETag"


def _ensure_dynamic_block_appids(doc: Drawing) -> None:
    for name in (
        AcDbDynamicBlockGUID,
        AcDbDynamicBlockTrueName,
        AcDbBlockRepETag,
        AcDbBlockRepBTag,
    ):
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


def _ensure_property_attdef_metadata(attdef, rep_index: int) -> None:
    doc = attdef.doc
    if doc is None:
        raise const.DXFStructureError("valid DXF document required")
    if "AcadAnnotative" not in doc.appids:
        doc.appids.new("AcadAnnotative")

    attdef.set_xdata(AcDbBlockRepETag, [(1070, 1), (1071, rep_index), (1005, "0")])
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


def get_dynamic_block_properties_table(
    source: Union[Insert, BlockLayout, BlockRecord], doc: Optional[Drawing] = None
) -> Optional[DynamicBlockPropertiesTable]:
    block_record = _resolve_dynamic_block_record(source, doc)
    if block_record is None:
        return None
    graph = _get_enhanced_block_graph(block_record)
    if graph is None:
        return None
    for entity in _iter_graph_owned_objects(graph):
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
) -> list[tuple[int, Any]]:
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
        if index == 0:
            tags.extend([(95, 2), (333, properties_grip_handle), (333, properties_table_handle)])
        else:
            tags.extend([(95, 1), (333, properties_grip_handle)])
    return tags


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
    visibility = get_dynamic_block_visibility_parameter(block)
    if visibility is None:
        raise const.DXFValueError("dynamic block has no visibility parameter")

    resolved_columns = _resolve_property_table_columns(block, table, visibility)
    _tag_block_representation_entities(block)
    for index, entity in enumerate(block):
        if entity.dxftype() == "ATTDEF":
            _ensure_property_attdef_metadata(entity, index)
            entity.dxf.discard("invisible")
    _delete_graph_stack(block.block_record)

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

    # Patch the visibility parameter with the actual table handle once it exists.
    vis_subclass = visibility_entity.xtags.get_subclass("AcDbBlockVisibilityParameter")
    patched_tags = _build_property_visibility_parameter_subclass(
        visibility,
        table_entity.dxf.handle,
        grip.dxf.handle,
    )
    vis_subclass.clear()
    from ezdxf.lldxf.types import dxftag

    vis_subclass.extend(dxftag(code, value) for code, value in patched_tags)

    eval_graph = graph.xtags.get_subclass("AcDbEvalGraph")
    handles = [
        visibility_entity.dxf.handle,
        proxy.dxf.handle,
        table_entity.dxf.handle,
        grip.dxf.handle,
        x_comp.dxf.handle,
        y_comp.dxf.handle,
    ]
    handle_index = 0
    for index, tag in enumerate(eval_graph):
        if tag.code == 360 and handle_index < len(handles):
            from ezdxf.lldxf.types import dxftag

            eval_graph[index] = dxftag(360, handles[handle_index])
            handle_index += 1

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


def set_dynamic_block_reference(block: BlockLayout, dynamic_block: BlockLayout) -> None:
    """Mark `block` as an anonymous representation of `dynamic_block`."""
    if block.doc is None:
        raise const.DXFStructureError("valid DXF document required")
    _ensure_dynamic_block_appids(block.doc)
    if not block.block_record.has_extension_dict:
        block.block_record.new_extension_dict()
    _clone_property_attdefs_to_reference(block, dynamic_block)
    _tag_block_representation_entities(block)
    for index, entity in enumerate(block):
        if entity.dxftype() == "ATTDEF":
            _ensure_property_attdef_metadata(entity, index)
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
