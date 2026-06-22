import bpy
from mathutils import Matrix
from bpy.types import PropertyGroup, Object
from bpy.props import IntProperty, CollectionProperty, PointerProperty


def _get_album_scale(self):
    """Read back from obj.scale.x, so the displayed value stays correct
    even if the album's scale was changed directly (e.g. dragging the
    empty's scale in the N-panel) instead of through this property."""
    obj = self.id_data
    if obj is None or obj.scale.x == 0:
        return 1
    return max(1, round(1.0 / obj.scale.x))


def _set_album_scale(self, value):
    """Apply the scale denominator to the album empty's X/Y/Z, then reset
    matrix_parent_inverse on every child so the album's transform always
    applies, regardless of whether they were parented before or after this
    scale value was set. Applies to any child object (mesh, grease pencil,
    image empty, etc.), not just MaStro drawings."""
    obj = self.id_data
    if obj is None:
        return
    factor = 1.0 / value
    obj.scale.x = factor
    obj.scale.y = factor
    obj.scale.z = factor
    for child in obj.children:
        child.matrix_parent_inverse = Matrix.Identity(4)


class mastro_CL_album_child_ref(PropertyGroup):
    """A single row in mastro_CL_album_settings.children_display.

    Rebuilt from obj.children on every panel draw — not a persisted
    relationship, just a UIList-compatible view over the real parenting."""
    object: PointerProperty(type=Object)


def _on_album_children_display_index_changed(self, context):
    """Select/activate the object picked in the children UIList."""
    if 0 <= self.children_display_index < len(self.children_display):
        obj = self.children_display[self.children_display_index].object
        if obj is not None:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj


class mastro_CL_album_settings(PropertyGroup):
    """Lives on a MaStro album Empty as obj.mastro_album_settings.

    scale is read by the children's Geometry Nodes (via an Object Info node
    pointing at the parent) so every child instance can render at the scale
    carried by its own album, instead of a single value baked into the node."""
    scale: IntProperty(
        name="Scale 1:",
        description="Scale denominator (e.g. 100 for 1:100) applied to children of this album",
        default=1,
        min=1,
        get=_get_album_scale,
        set=_set_album_scale,
    )

    children_display: CollectionProperty(type=mastro_CL_album_child_ref)
    children_display_index: IntProperty(default=0, update=_on_album_children_display_index_changed)
