.. _modify_entity_content:

Modify Entity Content
=====================

TODO

TEXT Entity
-----------

TODO

MTEXT Entity
------------

TODO

DIMENSION  Entity
-----------------

Delete the existing DIMENSION and create a new one.

MLEADER Entity
--------------

Delete the existing MLEADER and create a new one.

ACAD_TABLE Entity
-----------------

The current `ACAD_TABLE` support is intentionally small. It supports
text-table authoring plus a validated minimal block-cell helper, while richer
linked attributed block-cell authoring is still experimental.

Create a text-only table by::

    table = msp.add_table((0, 0), [["TITLE", "STATUS"], ["HEADER", "VALUE"]])

Resize rows and columns by::

    table.set_row_height(0, 20.0)
    table.set_col_width(1, 28.0)

Toggle title or header semantics by::

    table.set_title_suppressed(True)
    table.set_column_header_suppressed(True)

Update text-cell content by::

    table.set_cell_text(1, 1, "VALUE-LONG")

Text cells can also host object-backed field wrappers. For example::

    line = msp.add_line((0, 0), (3, 4))
    table.new_cell_acvar_field(0, 0, "Author", text="----")
    table.new_cell_dwgprops_field(1, 0, "Project", text="Demo")
    table.new_cell_acobjprop_field(1, 1, line, "Length", text="5.0")

These helpers are limited to text cells. They create the same wrapper/child
`FIELD` object structure used by the existing `TEXT` and `MTEXT` field APIs and
store the wrapper handle in the cell-level `344` shell tag.

Inline MTEXT-style payload formatting can also be authored directly by helper
methods. For example::

    table.set_cell_content_color(1, 0, 215, 10507177)

Local semantic fill/background overrides can be authored by::

    table.set_cell_fill_color(0, 1, 217, 9643919)

The validated disabled/no-fill state can be authored by::

    table.clear_cell_fill(0, 1)

or equivalently by::

    table.set_cell_fill_enabled(0, 1, False)

The older `set_cell_text_color()` name is retained as a compatibility alias for
the same validated semantic fill override surface.

Local text-style overrides can be authored by::

    table.set_cell_text_style(0, 1, "TABLE_ALT")

The current minimal block-cell authoring helper can replace a text cell by a
block cell without linked `TABLECONTENT` or block attributes::

    table.set_cell_block(2, 0, "TABLE_BLOCK_CELL_MIN")

These helpers rebuild the anonymous `*T` geometry block automatically so the
visible block content stays consistent with the semantic table shell.

The higher-level `set_cell_block_attribs()` path can already create a DXF that
AutoCAD accepts, but ATTDEF-backed values are still normalized by AutoCAD on the
first save, so that attributed block-cell write path is not documented as fully
stable yet.

