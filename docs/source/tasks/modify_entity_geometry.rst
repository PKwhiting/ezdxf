.. _modify_entity_geometry:

Modify Geometry of DXF Entities
================================

TODO

LINE 
----

TODO

CIRCLE
------

TODO

ARC
---

TODO

ELLIPSE
-------

TODO

SPLINE
------

TODO

LWPOLYLINE
----------

TODO

POLYLINE
--------

TODO

MESH
----

TODO

HATCH
-----

TODO

DIMENSION
---------

Delete the existing DIMENSION and create a new one.

MLEADER
-------

Delete the existing MLEADER and create a new one.

ACAD_TABLE
----------

The current `ACAD_TABLE` support does not expose direct low-level geometry
editing of the anonymous `*T` block.

Instead, use the table mutation helpers which update the semantic table cell
data and rebuild that block automatically, for example::

    table.set_cell_text(0, 0, "TITLE-LONG")
    table.set_cell_text_height(0, 0, 20.0)
    table.set_cell_alignment(0, 1, 4)

This is the supported way to modify text-only `ACAD_TABLE` geometry authored by
`ezdxf`.

