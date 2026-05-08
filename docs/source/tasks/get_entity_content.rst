
.. _get_entity_content:

Get Content From DXF Entities
=============================

TEXT Entity
-----------

The content of the TEXT entity is stored in a single DXF attribute :attr:`Text.dxf.text` 
and has an empty string as default value:

.. code-block:: Python

    for text in msp.query("TEXT"):
        print(text.dxf.text)

The :meth:`~ezdxf.entities.Text.plain_text` method returns the content of the TEXT 
entity without formatting codes.

.. seealso::

    **Classes**

    - :class:`ezdxf.entities.Text`

    **Tutorials**

    - :ref:`tut_text`

MTEXT Entity
------------

The content of the MTEXT entity is stored in multiple DXF attributes. The content can be 
accessed by the read/write property :attr:`~ezdxf.entities.MText.text` and the DXF attribute 
:attr:`MText.dxf.text` and has an empty string as default value:

.. code-block:: Python

    for mtext in msp.query("MTEXT"):
        print(mtext.text)
        # is the same as:
        print(mtext.dxf.text)

.. important::

    The line ending character ``\n`` will be replaced automatically by the MTEXT line 
    ending ``\P``.

The :meth:`~ezdxf.entities.MText.plain_text` method returns the content of the MTEXT 
entity without inline formatting codes.

.. seealso::

    **Classes**

    - :class:`ezdxf.entities.MText`
    - :class:`ezdxf.tools.text.MTextEditor`

    **Tutorials**

    - :ref:`tut_mtext`

MLEADER Entity
--------------

The content of MLEADER entities is stored in the :attr:`MultiLeader.context` object.  
The MLEADER contains text content if the :attr:`context.mtext` attribute is not ``None`` 
and block content if the :attr:`context.block` attribute is not ``None``

.. seealso::

    **Classes**

    - :class:`ezdxf.entities.MultiLeader`
    - :class:`ezdxf.entities.MLeaderContext`
    - :class:`ezdxf.entities.MTextData`
    - :class:`ezdxf.entities.BlockData`
    - :class:`ezdxf.entities.AttribData`

    **Tutorials**

    - :ref:`tut_mleader`

Text Content
~~~~~~~~~~~~

.. code-block:: Python

    for mleader in msp.query("MLEADER MULTILEADER"):
        mtext = mleader.context.mtext
        if mtext:
            print(mtext.insert)  # insert location
            print(mtext.default_content)  # text content

The text content supports the same formatting features as the MTEXT entity.

Block Content
~~~~~~~~~~~~~

The INSERT (block reference) attributes are stored in :attr:`MultiLeader.context.block` 
as :class:`~ezdxf.entities.BlockData`.

.. code-block:: Python

    for mleader in msp.query("MLEADER MULTILEADER"):
        block = mleader.context.block
        if block:
            print(block.insert)  # insert location


The ATTRIB attributes are stored outside the context object in :attr:`MultiLeader.block_attribs` 
as :class:`~ezdxf.entities.AttribData`.

.. code-block:: Python

    for mleader in msp.query("MLEADER MULTILEADER"):
        for attrib in mleader.block_attribs:
            print(attrib.text)  # text content of the ATTRIB entity


DIMENSION Entity
----------------

Get real measurement determined by definition points:

.. code-block:: Python

    for dimension in msp.query("DIMENSION"):
        print(str(dimension))
        print(f"Dimension Type: {dimension.dimtype}")
        print(f"Measurement: {dimension.get_measurement()}")

==== ============================== ===
Type Dimension Type                 Measurement
==== ============================== ===
0    Linear and Rotated Dimension   length in drawing units
1    Aligned Dimension              length in drawing units
2    Angular Dimension              angle in degree
3    Diameter Dimension             length in drawing units
4    Radius Dimension               length in drawing units
5    Angular 3P Dimension           angle in degree
6    Ordinate Dimension             feature location as :class:`~ezdxf.math.Vec3`
==== ============================== ===

Get measurement text. This is how the measurement text was rendered into the associated
geometry block by the CAD application as the DIMENSION entity was created:

.. code-block:: Python

    for dimension in msp.query("DIMENSION"):
        print(str(dimension))
        print(f"Measurement Text: {dimension.dxf.text}")

======== ===
Text     Measurement text rendered by CAD application
======== ===
``"<>"`` actual measurement
``""``   (empty string) actual measurement
``" "``  (space) measurement text is suppressed
other    measurement text entered by the CAD user
======== ===

Get measurement text from text entities in the associated geometry block. This is the
actual measurement text displayed by CAD applications:

.. code-block:: Python

    for dimension in msp.query("DIMENSION"):
        print(str(dimension))
        block = dimension.get_geometry_block()
        if block is None:
            print("Geometry block not found.")
            continue
        for entity in block.query("TEXT MTEXT"):
            print(f"{str(entity)}: {entity.dxf.text}")

.. seealso::

    **Tutorials:**

    - :ref:`tut_linear_dimension`

    **Classes:**

    - :class:`ezdxf.entities.Dimension`

ACAD_TABLE Entity
-----------------

The helper function :func:`read_acad_table_content` returns the content of an ACAD_TABLE
entity as list of table rows. If the count of table rows or table columns is missing the
complete content is stored in the first row. All cells contain strings.

.. code-block:: Python

    from ezdxf.entities.acad_table import read_acad_table_content

    ...

    for acad_table in msp.query("ACAD_TABLE"):
        content = read_acad_table_content(acad_table)
        for n, row in enumerate(content):
            for m, value in enumerate(row):
                print(f"cell [{n}, {m}] = '{value}'")

.. important::

    The ACAD_TABLE entity still has limited support compared to simpler DXF
    entities, but the current support is no longer read-only.

    Current authoring and modification support includes:

    - creating text-only tables by :meth:`layout.add_table() <ezdxf.graphicsfactory.CreatorInterface.add_table>`
    - resizing authored rows and columns by `set_row_height()` and `set_col_width()`
    - toggling title/header row semantics by `set_title_suppressed()` and `set_column_header_suppressed()`
    - updating text cell payloads by `set_cell_text()`
    - updating text cell local text-height overrides by `set_cell_text_height()`
    - updating text cell local alignment overrides by `set_cell_alignment()`
    - updating text cell local text-style overrides by `set_cell_text_style()`
    - updating text cell inline payload color formatting by `set_cell_content_color()`
    - updating text cell local fill/background overrides by `set_cell_fill_color()`
    - disabling text cell local fill/background by `clear_cell_fill()` or `set_cell_fill_enabled(..., False)`
    - setting a minimal block cell by `set_cell_block()`

    These mutation helpers rebuild the anonymous `*T` geometry block so the
    visible block content stays in sync with the semantic `AcDbTable` shell.

    Current read support includes:

    - row count and column count
    - row heights and column widths
    - ordered text cell content
    - a readable subset of explicit cell-local overrides such as text height
      and alignment
    - linked block-cell attribute payloads through the associated `TABLECONTENT`
      object, when present
    - wrapper-geometry fallback resolution for block-cell `ATTRIB` values kept by
      AutoCAD after linked attributed payload normalization
    - typed access to the associated `TABLESTYLE` object through the loaded
      `TABLESTYLE` entity and the document collection `doc.table_styles`

    The linked table content object itself is also loaded as a typed
    `TABLECONTENT` object and can be queried from an `ACAD_TABLE` entity by the
    helper methods added on the loaded table entity.
    Readable linked row, column, and formatted cell wrapper structures are also
    preserved in that typed `TABLECONTENT` layer.

    For example::

        linked_col = acad_table.get_linked_column(0)
        linked_row = acad_table.get_linked_row(0)
        linked_cell = acad_table.get_linked_cell(0, 0)

    Some visual text formatting, such as content color, can also be stored
    inline in the cell text payload itself, similar to MTEXT formatting codes.

    Block-cell payloads can also be queried from loaded tables. For example,
    if a block cell contains ATTDEF-backed values stored in linked table
    content, or if AutoCAD has normalized those values into wrapper-block
    `ATTRIB` entities after a save, the resolved tag/value mapping for a cell can
    be obtained by::

        cell = acad_table.get_cell(2, 0)
        attribs = acad_table.get_cell_block_attribs(2, 0)

    If a text cell references a `FIELD` object by handle, the linked field can
    be resolved from the loaded table as well::

        field = acad_table.get_cell_field(0, 0)
        primary_field = acad_table.get_cell_primary_field(0, 0)

    If the primary field is an `AcExpr` expression field, the operand fields can
    be traversed by::

        if primary_field and primary_field.evaluator_id == "AcExpr":
            operands = primary_field.get_child_fields()

    Table text cells authored by `ezdxf` can also create these field wrappers
    directly by::

        line = table.doc.modelspace().add_line((0, 0), (3, 4))
        table.new_cell_acvar_field(0, 0, "Author", text="----")
        table.new_cell_acobjprop_field(1, 0, line, "Length", text="5.0")

    Expression fields can also be authored by supplying child `FIELD` objects
    explicitly. For example::

        from ezdxf.entities.dxfobj import Field

        circle = table.doc.modelspace().add_circle((5, 0), radius=2.5)
        child1 = Field()
        child1.set_acobjprop(line, "Length", value=10.0, display="10.0000")
        child2 = Field()
        child2.set_acobjprop(circle, "Radius", value=2.5, display="2.5000")
        table.new_cell_acexpr_field(
            2,
            0,
            "(%<\\_FldIdx 0>%*%<\\_FldIdx 1>%)",
            [child1, child2],
            value=25.0,
            text="25.0000",
        )

    The associated `TABLESTYLE` object and the default Title/Header/Data row
    style buckets can also be resolved from a loaded table::

        style = acad_table.get_table_style()
        title_bucket = acad_table.get_row_style_bucket(0)

    New documents also expose the `TABLESTYLE` object collection at
    `doc.table_styles`.

    Example authoring flow::

        table = msp.add_table((0, 0), [["TITLE", "STATUS"], ["HEADER", "VALUE"]])
        table.set_cell_text(1, 1, "VALUE-LONG")
        table.set_col_width(1, 28.0)
        table.set_row_height(0, 20.0)
        table.set_title_suppressed(True)
        table.set_cell_text_height(0, 0, 20.0)
        table.set_cell_alignment(0, 1, 4)
        table.set_cell_text_style(1, 0, "TABLE_ALT")
        table.set_cell_content_color(1, 0, 215, 10507177)
        table.set_cell_fill_color(0, 1, 217, 9643919)
        table.clear_cell_fill(0, 1)
        table.set_cell_block(2, 0, "TABLE_BLOCK_CELL_MIN")

INSERT Entity - Block References
--------------------------------

Get Block Attributes
~~~~~~~~~~~~~~~~~~~~

Get a block attribute by tag:

.. code-block:: Python

    diameter = insert.get_attrib('diameter')
    if diameter is not None:
        print(f"diameter = {diameter.dxf.text}")

Iterate over all block attributes:

.. code-block:: Python

    for attrib in insert.attribs:
        print(f"{attrib.dxf.tag} = {attrib.dxf.text}")

.. important::

    Do not confuse block attributes and DXF entity attributes, these are different
    concepts!

Get Block Entities
~~~~~~~~~~~~~~~~~~

Get block entities as virtual DXF entities from an :class:`~ezdxf.entities.Insert` entity:

.. code-block:: Python

    for insert in msp.query("INSERT"):
        for entity in insert.virtual_entities():
            print(str(entity))

Get Transformation Matrix
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: Python

    m = insert.matrix44()

This transformation matrix transforms the virtual block entities from the block reference
coordinate system into the :ref:`WCS`.

.. seealso::

    **Tasks:**

    - :ref:`add_blockrefs`
    - :ref:`explode_block_references`

    **Tutorials:**

    - :ref:`tut_blocks`

    **Basics:**

    - :ref:`block_concept`

    **Classes:**

    - :class:`ezdxf.entities.Insert`
    - :class:`ezdxf.entities.Attrib`
    - :class:`ezdxf.entities.AttDef`
    - :class:`ezdxf.math.Matrix44`
