import bpy
from .update_bmesh_drawing_attributes import update_bmesh_drawing_attributes
from .drawing_materials import ensure_layer_material


def update_layer(self, context):
    """Called when any property of a MASTRO_Layer changes."""
    ensure_layer_material(context.scene, self.layer_id)
    update_bmesh_drawing_attributes(context, layer_ids={self.layer_id})


def update_pen(self, context):
    """Called when pen thickness or colour changes.

    Only propagates to layers that reference this pen.
    """
    pen_id = self.pen_id
    scene = context.scene
    layer_ids = {l.layer_id for l in scene.mastro_cad_layers if l.pen_id == pen_id}
    if layer_ids:
        for lid in layer_ids:
            ensure_layer_material(scene, lid)
        update_bmesh_drawing_attributes(context, layer_ids=layer_ids)


def update_pattern(self, context):
    """Called when a dash pattern's slots change.

    Only propagates to layers that reference this pattern.
    """
    pattern_id = self.pattern_id
    layer_ids = {
        l.layer_id
        for l in context.scene.mastro_cad_layers
        if l.pattern_id == pattern_id
    }
    if layer_ids:
        update_bmesh_drawing_attributes(context, layer_ids=layer_ids)
