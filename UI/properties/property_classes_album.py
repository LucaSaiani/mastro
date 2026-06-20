from mathutils import Matrix
from bpy.types import PropertyGroup
from bpy.props import IntProperty


def _on_album_scale_changed(self, context):
    """Apply the scale denominator to the album empty's X/Y, then reset
    matrix_parent_inverse on every child so the album's transform always
    applies, regardless of whether they were parented before or after this
    scale value was set. Applies to any child object (mesh, grease pencil,
    image empty, etc.), not just MaStro drawings."""
    obj = context.object
    if obj is None:
        return
    factor = 1.0 / self.scale
    obj.scale.x = factor
    obj.scale.y = factor
    for child in obj.children:
        child.matrix_parent_inverse = Matrix.Identity(4)


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
        update=_on_album_scale_changed,
    )
