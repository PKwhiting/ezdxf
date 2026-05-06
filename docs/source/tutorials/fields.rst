.. _tut_fields:

Tutorial for Fields
===================

The current experimental field API can create object-backed AutoCAD-style field
graphs for several host entities.

Supported field hosts
---------------------

- :class:`~ezdxf.entities.MText`
- :class:`~ezdxf.entities.Text`
- :class:`~ezdxf.entities.MultiLeader` with MTEXT content
- :class:`~ezdxf.entities.AttDef`
- :class:`~ezdxf.entities.Attrib`

Supported field families
------------------------

- ``AcVar``
- ``DWGPROPS`` via the observed ``AcVar CustomDP.<Name>`` pattern
- ``AcObjProp``

Support model
-------------

There are two different support layers:

- structural DXF support for object-backed ``FIELD`` and ``FIELDLIST`` objects
- selective high-level authoring support for specific field hosts and specific
  field/property cases

This means `ezdxf` can build and preserve object-backed field graphs in general,
but only a validated subset of field families and object-property cases are
exposed by the current convenience API.

`ezdxf` does not evaluate fields by itself. AutoCAD is still the authoritative
field evaluator in the current workflow.

Host / family matrix
--------------------

.. list-table::
    :header-rows: 1

    * - Host
      - ``AcVar``
      - ``DWGPROPS``
      - ``AcObjProp``
      - Notes
    * - :class:`~ezdxf.entities.MText`
      - yes
      - yes
      - yes
      - object-backed host with dedicated layout helpers
    * - :class:`~ezdxf.entities.Text`
      - yes
      - yes
      - yes
      - also covers ``ATTRIB`` and ``ATTDEF`` entity-level helpers
    * - :class:`~ezdxf.entities.MultiLeader`
      - yes
      - yes
      - yes
      - MTEXT-content leaders only
    * - :class:`~ezdxf.entities.AttDef`
      - yes
      - yes
      - yes
      - stand-alone attribute definitions
    * - :class:`~ezdxf.entities.Attrib`
      - yes
      - yes
      - yes
      - attached to ``INSERT`` entities

Object-property support matrix
------------------------------

.. list-table::
    :header-rows: 1

    * - Entity
      - Supported properties
      - Notes
    * - ``LINE``
      - ``Length``
      - exact
    * - ``ARC``
      - ``Radius``, ``Length``, ``ArcLength``, ``Area``
      - exact
    * - ``CIRCLE``
      - ``Radius``, ``Diameter``, ``Circumference``, ``Area``
      - exact
    * - ``ELLIPSE``
      - ``MajorRadius``, ``MinorRadius``, ``Area``
      - exact for full ellipses and ellipse arcs
    * - ``SPLINE``
      - ``Area``
      - planar splines only; approximation-based
    * - ``POLYLINE``
      - ``Length``, ``Area``
      - 2D polylines with straight or circular-arc segments
    * - ``POLYLINE``
      - ``Length``
      - 3D polylines only
    * - ``LWPOLYLINE``
      - ``Length``, ``Area``
      - 2D polylines with straight or circular-arc segments
    * - ``HATCH``
      - ``Area``
      - polyline boundary paths, simple non-bulged hole loops, and single line/arc/ellipse/spline edge paths

Drawing property fields
-----------------------

DWGPROPS-backed fields are currently authored through the observed
``CustomDP.<Name>`` namespace and also populate the underlying drawing property
store via :attr:`doc.header.custom_vars`.

Example:

.. code-block:: python

    import ezdxf

    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    msp.add_mtext_dwgprops_field(
        "ProjectCode",
        text="VALUE-123",
        dxfattribs={"insert": (0, 0, 0)},
        register_field_list=True,
    )

Object property fields
----------------------

The current automatic inference support is intentionally small and explicit.

Supported inferred object-property cases:

- ``LINE.Length``
- ``POLYLINE.Length`` for 3D polylines
- ``ELLIPSE.MajorRadius``
- ``ELLIPSE.MinorRadius``
- ``ELLIPSE.Area``
- ``ARC.Radius``
- ``ARC.Length``
- ``ARC.ArcLength``
- ``ARC.Area``
- ``SPLINE.Area`` for planar splines
- ``HATCH.Area`` for polyline boundary paths, including simple hole loops, and for single edge paths made of line/arc, ellipse, or spline edges
- ``POLYLINE.Length`` for 2D polylines with straight or circular-arc segments
- ``POLYLINE.Area`` for 2D polylines with straight or circular-arc segments
- ``LWPOLYLINE.Length`` for 2D polylines with straight or circular-arc segments
- ``LWPOLYLINE.Area`` for 2D polylines with straight or circular-arc segments
- ``CIRCLE.Radius``
- ``CIRCLE.Diameter``
- ``CIRCLE.Circumference``
- ``CIRCLE.Area``

Example:

.. code-block:: python

    import ezdxf

    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    line = msp.add_line((0, 0), (10, 0))
    msp.add_mtext_acobjprop_field(
        line,
        "Length",
        dxfattribs={"insert": (0, 0, 0)},
        register_field_list=True,
    )

Host-specific convenience methods
---------------------------------

Layout/modelspace level helpers:

- :meth:`~ezdxf.graphicsfactory.CreatorInterface.add_mtext_acvar_field`
- :meth:`~ezdxf.graphicsfactory.CreatorInterface.add_mtext_dwgprops_field`
- :meth:`~ezdxf.graphicsfactory.CreatorInterface.add_mtext_acobjprop_field`
- :meth:`~ezdxf.graphicsfactory.CreatorInterface.add_text_acvar_field`
- :meth:`~ezdxf.graphicsfactory.CreatorInterface.add_text_dwgprops_field`
- :meth:`~ezdxf.graphicsfactory.CreatorInterface.add_text_acobjprop_field`

Entity-level helpers:

- :meth:`~ezdxf.entities.MText.new_acvar_field`
- :meth:`~ezdxf.entities.MText.new_dwgprops_field`
- :meth:`~ezdxf.entities.MText.new_acobjprop_field`
- :meth:`~ezdxf.entities.Text.new_acvar_field`
- :meth:`~ezdxf.entities.Text.new_dwgprops_field`
- :meth:`~ezdxf.entities.Text.new_acobjprop_field`
- :meth:`~ezdxf.entities.MultiLeader.new_acvar_field`
- :meth:`~ezdxf.entities.MultiLeader.new_dwgprops_field`
- :meth:`~ezdxf.entities.MultiLeader.new_acobjprop_field`

Builder-level helpers for MTEXT MULTILEADER content:

- :meth:`~ezdxf.render.MultiLeaderMTextBuilder.set_acvar_field`
- :meth:`~ezdxf.render.MultiLeaderMTextBuilder.set_dwgprops_field`
- :meth:`~ezdxf.render.MultiLeaderMTextBuilder.set_acobjprop_field`

Known gaps
----------

- ``MULTILEADER`` object-property child cache values still oscillate across
  repeated AutoCAD saves, even though the field graph survives.
- Raw multi-path bulged-hole ``HATCH.Area`` authoring is still not modeled.
- ``MPOLYGON.Area`` did not resolve in AutoCAD during probing.
- ``3DFACE`` and ``SOLID`` did not expose useful probed object-property cases.
- ``POLYLINE`` 3D ``Area`` did not resolve in AutoCAD during probing.
- ``SPLINE.Length`` and ``SPLINE.ArcLength`` did not resolve in AutoCAD during probing.
- Several intuitive names such as ``ARC.Diameter`` and ``ELLIPSE.Length`` are not supported by AutoCAD in the current probe set.

Validation artifact
-------------------

For a compact visual smoke test of the currently supported recent additions,
see:

- ``experiments/ezdxf-generated-fields/recent_supported_fields_validation.dxf``

Notes
-----

- The generated DXF is accepted by AutoCAD in the current validation matrix.
- Byte-level parity with UI-authored field graphs is still a work in progress.
- The automatic inference support is intentionally conservative and will expand
  only when backed by concrete experiments.
