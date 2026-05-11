import ezdxf

from ezdxf.entities import BlockRecord
from ezdxf.lldxf.tagwriter import TagCollector


BLOCK_RECORD_WITH_BLKREFS = """0
BLOCK_RECORD
5
4A
102
{ACAD_XDICTIONARY
360
58
102
}
330
9
100
AcDbSymbolTableRecord
100
AcDbBlockTableRecord
2
*U1
340
0
102
{BLKREFS
331
59
102
}
70
0
280
1
281
0
"""


def test_loads_blkrefs_handles_from_block_record():
    entity = BlockRecord.from_text(BLOCK_RECORD_WITH_BLKREFS)

    assert entity.dxf.name == "*U1"
    assert entity.blkref_handles == ["59"]


def test_exports_blkrefs_handles_in_block_record_order():
    doc = ezdxf.new("R2018")
    block = doc.blocks.new_anonymous_block(type_char="U")
    block.block_record.blkref_handles = ["59"]

    collector = TagCollector(dxfversion=doc.dxfversion)
    block.block_record.export_dxf(collector)
    tags = collector.tags

    assert (102, "{BLKREFS") in tags
    blkrefs_index = tags.index((102, "{BLKREFS"))
    assert tags[blkrefs_index + 1] == (331, "59")
    assert tags[blkrefs_index + 2] == (102, "}")
