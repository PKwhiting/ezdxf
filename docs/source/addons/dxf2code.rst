.. module:: ezdxf.addons.dxf2code

.. _dxf2code:

dxf2code
========

Translate DXF entities and structures into Python source code.

`dxf2code` recreates the translated entity graph, including simple object-backed
``FIELD`` wrappers hosted by ``TEXT``, ``ATTRIB``, ``ATTDEF`` and ``MTEXT``.
For ``AcObjProp`` fields, the referenced target entity also has to be part of
the translated entity set so the new field payload can be rebound to the new
handles in the generated document.

`dxf2code` also recreates ``MULTILEADER`` entities by rebuilding the nested
context and leader-line structures in generated code.
Hosted ``FIELD`` wrappers are preserved for MTEXT-content multileaders by the
same deferred field reconstruction used for other supported text hosts.
The generated code resolves the referenced ``MLEADERSTYLE``, text style and
linetype by name in the target document. Missing referenced ``MLEADERSTYLE``
entries are recreated in generated code from the source style data before the
``MULTILEADER`` entity is rebuilt. Referenced arrow-head blocks on the style or
on the ``MULTILEADER`` entity itself are rebound by block name as well.
Referenced non-arrow style blocks are rebound if the target document already
contains the matching block definition; otherwise that optional style handle is
omitted to avoid failing code generation.

For BLOCK-content multileaders the referenced block definition still has to
exist in the target document, just like normal block references. The generated
code remaps virtual block-attribute handles to the target block ATTDEF handles
by ATTDEF order.
Additional ``MultiLeader.arrow_heads`` collections are also rebound by block
name.

Short example:

.. code-block:: Python

    import ezdxf
    from ezdxf.addons.dxf2code import entities_to_code, block_to_code

    doc = ezdxf.readfile('original.dxf')
    msp = doc.modelspace()
    source = entities_to_code(msp)

    # create source code for a block definition
    block_source = block_to_code(doc.blocks['MyBlock'])

    # merge source code objects
    source.merge(block_source)

    with open('source.py', mode='wt') as f:
        f.write(source.import_str())
        f.write('\n\n')
        f.write(source.code_str())
        f.write('\n')


.. autofunction:: entities_to_code

.. autofunction:: block_to_code

.. autofunction:: table_entries_to_code

.. autofunction:: black

.. class:: Code

    Source code container.

    .. attribute:: code

        Source code line storage, store lines without line ending ``\\n``

    .. attribute:: imports

        source code line storage for global imports, store lines without line ending ``\\n``

    .. attribute:: layers

        Layers used by the generated source code, AutoCAD accepts layer names without a LAYER table entry.

    .. attribute:: linetypes

        Linetypes used by the generated source code, these linetypes require a TABLE entry or AutoCAD will crash.

    .. attribute:: styles

        Text styles used by the generated source code, these text styles require a TABLE entry or AutoCAD will crash.

    .. attribute:: dimstyles

        Dimension styles  used by the generated source code, these dimension styles require a TABLE entry or AutoCAD will crash.

    .. attribute:: blocks

        Blocks used by the generated source code, these blocks require a BLOCK definition in the BLOCKS section or AutoCAD will crash.

    .. automethod:: code_str

    .. automethod:: black_code_str

    .. automethod:: import_str

    .. automethod:: merge

    .. automethod:: add_import

    .. automethod:: add_line

    .. automethod:: add_lines


