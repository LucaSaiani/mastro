import bpy
import bmesh
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy_extras import object_utils
from ..mastro_custom_properties.OBJECT_OT_Update_Mastro_Custom_Properties import add_custom_properties_to_object

from ...Utils.mastro_arch.add_attributes_plan import add_plan_attributes
from ...Utils.mastro_arch.update_plan_attributes import update_plan_attributes
from ...Utils.mastro_arch.plan_drivers import link_all_plan_drivers
from ...Utils.add_nodes import add_nodes, add_materials
from ...Utils.mastro_levels.clip_range import active_clip_range_level_id


class OBJECT_OT_Add_Mastro_Plan(Operator, AddObjectHelper):
    """Add a MaStro plan"""
    bl_idname = "object.mastro_add_mastro_plan"
    bl_label = "Plan"
    bl_options = {'REGISTER', 'UNDO'}

    width: bpy.props.FloatProperty(
        name="Width",
        description="MaStro plan width",
        min=0,
        default=10,
    )

    depth: bpy.props.FloatProperty(
        name="Depth",
        description="MaStro plan depth",
        min=0,
        default=10,
    )

    def execute(self, context):
        verts = [
        (+0.0, +0.0,  +0.0),
        (+1.0, +0.0,  +0.0),
        (+1.0, +1.0,  +0.0),
        (+0.0, +1.0,  +0.0),
        ]

        faces = [
            (0, 1, 2, 3),
        ]

        # apply size
        for i, v in enumerate(verts):
            verts[i] = v[0] * self.width, v[1] * self.depth, v[2]

        mesh = bpy.data.meshes.new("MaStro plan")

        bm = bmesh.new()

        for v_co in verts:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in faces:
            bm.faces.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        object_utils.object_data_add(context, mesh, operator=self)

        obj = bpy.context.active_object

        add_nodes()
        add_materials()

        bm.free()

        # add mastro plan geo node to the created object
        geoName = "MaStro Plan"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Plan"]
        obj.modifiers[geoName].node_group = group

        # modifier.properties.inputs is only populated after Blender syncs the
        # modifier with the node group interface; force that sync now so the
        # drivers below can find the input sockets.
        context.view_layer.update()

        context.view_layer.objects.active = obj

        obj.select_set(True)

        add_plan_attributes(obj)
        add_custom_properties_to_object(obj, is_street=False, is_plan=True)

        # New plans are locked to a level by default (see add_plan_attributes),
        # so wire up the FFL -> location.z and Floor to Floor Height -> GN
        # input drivers right away.
        link_all_plan_drivers(obj, obj.modifiers[geoName])

        # Plans are always created at the active (bottom) level's elevation
        # (unlike MaStro drawing, this ignores the create_drawing_at_active_level
        # preference - a plan never makes sense floating at the 3D cursor's Z).
        # X/Y stay wherever object_data_add put the object (the 3D cursor).
        # Z, top_level_id and floor_to_floor_height are then derived by the
        # same function used to keep plans in sync when levels change later.
        bottom_level_id = active_clip_range_level_id(context)
        if bottom_level_id is not None:
            obj.mastro_props.mastro_bottom_level_id = bottom_level_id
            update_plan_attributes(context)

        # Lock Z so the plan can't be accidentally moved off its level.
        obj.lock_location[2] = True

        return {'FINISHED'}
