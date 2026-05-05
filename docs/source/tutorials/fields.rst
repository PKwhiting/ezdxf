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
- ``ELLIPSE.MajorRadius``
- ``ELLIPSE.MinorRadius``
- ``ELLIPSE.Area``
- ``ARC.Radius``
- ``ARC.Length``
- ``ARC.ArcLength``
- ``ARC.Area``
- ``LWPOLYLINE.Length`` for straight-segment polylines
- ``LWPOLYLINE.Area`` for closed straight-segment polylines
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

Notes
-----

- The generated DXF is accepted by AutoCAD in the current validation matrix.
- Byte-level parity with UI-authored field graphs is still a work in progress.
- The automatic inference support is intentionally conservative and will expand
  only when backed by concrete experiments.
