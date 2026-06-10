from bpy.types import PropertyGroup
from bpy.props import (BoolProperty,
                       StringProperty,
)


def _sync_note_text(self, context):
    """Push text_content into the linked bpy.data.texts block."""
    node_tree = getattr(getattr(context, 'space_data', None), 'edit_tree', None)
    if node_tree is None:
        return
    active = node_tree.nodes.active
    if active is None or not getattr(active, 'text', None):
        return
    text_block = active.text
    text_block.clear()
    text_block.write(self.text_content)


class mastro_CL_Sticky_Note(PropertyGroup):
    """Marks a NodeFrame as a MaStro sticky note so it can be styled and identified."""
    customNote: BoolProperty(
        name="Custom Note",
        description="Indicates if this NodeFrame is a custom sticky note",
        default=False
    )
    text_content: StringProperty(
        name="Note",
        description="Sticky note text — synced to the NodeFrame text block",
        default="",
        update=_sync_note_text,
    )
