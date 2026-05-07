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

The current `ACAD_TABLE` support is intentionally small and limited to
text-only tables authored by `ezdxf`, but basic content updates are supported.

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

These helpers rebuild the anonymous `*T` geometry block automatically so the
visible block content stays consistent with the semantic table shell.

