import bpy
import bmesh
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper
from ...Utils.mastro_cad.add_attributes_drawing import add_drawing_attributes
from ...Utils.mastro_cad.update_bmesh_drawing_attributes import update_bmesh_drawing_attributes
from ...Utils.mastro_cad.drawing_materials import ensure_all_layer_materials
from ...Nodes.operators.NODE_OT_MaStro_Drawing_GN import build_drawing_gn


class OBJECT_OT_MaStroCad_Add_Drawing_Mesh(Operator, AddObjectHelper):
    """Add a MaStro drawing (Mesh)"""
    bl_idname = "mastrocad.add_drawing_mesh"
    bl_label  = "MaStro Drawing (Mesh)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        me = bpy.data.meshes.new("MaStro drawing")

        bm = bmesh.new()
        v0 = bm.verts.new((0.0, 0.0, 0.0))
        v1 = bm.verts.new((0.0, 1.0, 0.0))
        bm.edges.new((v0, v1))
        bm.to_mesh(me)
        bm.free()

        obj = bpy.data.objects.new("MaStro drawing", me)
        obj.location = context.scene.cursor.location
        context.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        me["MaStro object"]       = True
        me["MaStro drawing"]      = True
        me["MaStro drawing mesh"] = True

        add_drawing_attributes(obj)

        # Assign the active layer and push its values onto the edge. Use the
        # 3D View sidebar's active layer (window_manager), consistent with
        # the extrusion handler — not the Scene Properties panel's index.
        scene_layers = context.scene.mastro_cad_layers
        idx = context.window_manager.mastro_cad_viewport_layer_index
        active_layer_id = scene_layers[idx].layer_id if scene_layers and 0 <= idx < len(scene_layers) else 0
        me.attributes["mastro_drawing_layer"].data[0].value = active_layer_id
        update_bmesh_drawing_attributes(context, {active_layer_id})

        scene = context.scene
        ensure_all_layer_materials(scene)
        layers = [(l.layer_id, l.name) for l in scene.mastro_cad_layers]
        mod = obj.modifiers.new("MaStro Drawing Mesh", 'NODES')
        mod.node_group = build_drawing_gn(layers, scene=scene)

        return {'FINISHED'}
