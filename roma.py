bl_info = {
    "name" : "RoMa",
    "author" : "Luca Saiani <luca.saiani@gmail.com",
    "version" : (0,1),
    "blender" : (3,0,0),
    "category" : "Object",
    "location" : "View3D > Add > Mesh > Road",
    "description" : "Adds roads and buildings to develop master plans",
    "warning" : "",
    "doc_url" : "",
    "tracker_url" : "",
}

import bpy, bpy.props, bpy_extras
from mathutils import Vector

def add_road(self, context):
    scale_x = self.scale.x
    scale_y = self.scale.y

    verts = [
        Vector((0, 0, 0)),
        Vector((10 * scale_x, 0, 0)),
    ]

    edges = [[0,1]]
    faces = []

    mesh = bpy.data.meshes.new(name="Road")
    mesh.from_pydata(verts, edges, faces)
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    road = bpy_extras.object_utils.object_data_add(context, mesh, operator=self)
    road.hide_render = True

def add_building(self, context):
    scale_x = self.scale.x
    scale_y = self.scale.y

    verts = [
        Vector((-0.5 * scale_x, -0.5 * scale_y, 0)),
        Vector((0.5 * scale_x, -0.5 * scale_y, 0)),
        Vector((0.5 * scale_x, 0.5 * scale_y, 0)),
        Vector((0 * scale_x, 0.9 * scale_y, 0)),
        Vector((-0.5 * scale_x, 0.5 * scale_y, 0))
    ]

    edges = [[0,1], [1,2], [2,3], [3,4], [4,0]]
    faces = []

    mesh = bpy.data.meshes.new(name="Building")
    mesh.from_pydata(verts, edges, faces)

    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    building = bpy_extras.object_utils.object_data_add(context, mesh, operator=self)
    building.hide_render = True
    building.lock_rotation = (True, True, True)
    building.lock_rotation_w = True


class OBJECT_OT_add_road(bpy.types.Operator, bpy_extras.object_utils.AddObjectHelper):
    """Add a road object"""
    bl_idname = "mesh.add_road"
    bl_label = "Add Road"
    bl_options = {'REGISTER', 'UNDO'}

    scale: bpy.props.FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    # shows the class only in the 3D view
    @classmethod
    def poll(cls, context):
        return context.area.type == "VIEW_3D"

    def execute(self, context):
        add_road(self, context)
        return {'FINISHED'}

class OBJECT_OT_add_building(bpy.types.Operator, bpy_extras.object_utils.AddObjectHelper):
    """Add a building object"""
    bl_idname = "mesh.add_building"
    bl_label = "Add Building"
    bl_options = {'REGISTER', 'UNDO'}

    scale: bpy.props.FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    # shows the class only in the 3D view
    @classmethod
    def poll(cls, context):
        return context.area.type == "VIEW_3D"

    def execute(self, context):
        add_building(self, context)
        return {'FINISHED'}

#registration
def add_road_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_road.bl_idname,
        text="Add Road",
        icon='IPO_EASE_IN_OUT')

def add_building_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_building.bl_idname,
        text="Add Building",
        icon='IPO_EASE_IN_OUT')

def register():
    bpy.utils.register_class(OBJECT_OT_add_road)
    bpy.types.VIEW3D_MT_mesh_add.append(add_road_button)

    bpy.utils.register_class(OBJECT_OT_add_building)
    bpy.types.VIEW3D_MT_mesh_add.append(add_building_button)

def unregister():
    bpy.utils.register_class(OBJECT_OT_add_road)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_road_button)

    bpy.utils.register_class(OBJECT_OT_add_building)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_building_button)
