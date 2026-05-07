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

Update text-cell content by::

    table.set_cell_text(1, 1, "VALUE-LONG")

Inline MTEXT-style payload formatting can also be authored directly by helper
methods. For example::

    table.set_cell_content_color(1, 0, 215, 10507177)

Local semantic text-color overrides can be authored by::

    table.set_cell_text_color(0, 1, 217, 9643919)

These helpers rebuild the anonymous `*T` geometry block automatically so the
visible block content stays consistent with the semantic table shell.

