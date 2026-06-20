from bpy.types import Operator
from mathutils import Vector


def _bbox_world_center(obj):
    """World-space center of obj's bounding box."""
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return sum(corners, Vector()) / 8


class OBJECT_OT_Parent_to_Mastro_Album(Operator):
    """Parent the selected objects to the active MaStro album, without an
    inverse — so the child immediately picks up the album's current
    scale (no need to touch the album's Scale property again before a
    newly parented child reacts to it). Parenting without an inverse also
    shifts the child's world position by the album's existing scale
    around the album's origin, so afterwards we re-center the child back
    onto its own pre-parenting bounding box center."""
    bl_idname = "object.mastro_parent_to_album"
    bl_label = "Parent to MaStro Album"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        album = context.object
        return (album is not None and album.get("MaStro album")
                and len(context.selected_objects) > 1)

    def execute(self, context):
        album = context.object
        children = [obj for obj in context.selected_objects if obj is not album]

        for child in children:
            center_before = _bbox_world_center(child)

            child.parent = album
            child.matrix_parent_inverse.identity()
            context.view_layer.update()

            center_after = _bbox_world_center(child)
            child.location += child.matrix_world.to_3x3().inverted() @ (center_before - center_after)

        return {'FINISHED'}
