import bpy
import bmesh

from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import (
        AddObjectHelper,
        object_data_add
)
from mathutils import Vector
from bpy.types import (
#    Header,
#    Menu,
    Panel,
    Operator
)


bl_info = {
    "name": "ROMA Buildingz",
    "author": "Luca Saiani",
    "version": (1, 0),
    "blender": (3, 50, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Adds a new ROMA Building object",
    "warning": "",
    "doc_url": "",
    "category": "Add a Mesh",
}

previous_last_index = None


class OBJECT_OT_add_RoMa_Wall(Operator, AddObjectHelper):
    """Create a new RoMa Wall"""
    bl_idname = "mesh.add_object"
    bl_label = "Add RoMa Wall"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):

        add_RoMa_Wall(self, context)

        return {'FINISHED'}
    
class SetEdgeAttributeOperator(bpy.types.Operator):
    """Set Edge Attribute as Wall Type"""
    bl_idname = "object.set_edge_attribute_as_wall_type"
    bl_label = "Set Edge Attribute as Wall Type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_wall_type = context.scene.attribute_wall_type
        
        # a custom attribute is assigned to the edges
        try:
            mesh.attributes["Wall_Type"]
            # except:
            #     mesh.attributes.new(name="Wall_Type", type="FLOAT", domain="EDGE")

            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')

            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]

            mesh_attributes = mesh.attributes["Wall_Type"].data.items()

            for edge in selected_edges:
                index = edge.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_wall_type

            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to "+str(attribute_wall_type))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
    

class VIEW3D_PT_RoMa_Wall(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Wall:"
    
    def draw(self, context):
        
        layout = self.layout

        row = layout.row()
        row.prop(context.scene, "attribute_wall_type", text="Type")
        if context.active_object.mode=='EDIT':
            row.enabled = True
        else:
            row.enabled = False
            
def add_RoMa_Wall(self, context):
    scale_x = self.scale.x
    scale_y = self.scale.y

    verts = [
        Vector((0, 0, 0)),
        Vector((1 * scale_x, 0, 0))
    ]

    edges = [[0,1]]
    faces = []

    mesh = bpy.data.meshes.new(name="New RoMa Wall")
    mesh.from_pydata(verts, edges, faces)
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)
    mesh.attributes.new(name="Wall_Type", type="FLOAT", domain="EDGE")
    
def add_RoMa_Wall_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_RoMa_Wall.bl_idname,
        text="Add RoMa Wall",
        icon='PLUGIN')

# This allows you to right click on a button and link to documentation
# def add_RoMa_Wall_manual_map():
#     url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
#     url_manual_mapping = (
#         ("bpy.ops.mesh.add_object", "scene_layout/object/types.html"),
#     )
#     return url_manual_prefix, url_manual_mapping


def callback_edge_selected(context):
    global previous_last_index
    
    obj = bpy.context.active_object
    try:
        mesh.attributes["Wall_Type"]
        if obj.mode == 'EDIT':
            # Get the bmesh data
            bm = bmesh.from_edit_mesh(obj.data)

            # Get a list of all selected edges
            # selected_edges = [edge for edge in bm.edges if edge.select]
            selected_edges = []
            for edge in bm.edges:
                if edge.select:
                    selected_edges.append(edge)
                    last_index = edge.index
            if previous_last_index == None or previous_last_index != last_index:
                previous_last_index = last_index
                    
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh = obj.data
                sel_edges = [e for e in bpy.context.active_object.data.edges if e.select]
                mesh_attributes = mesh.attributes["Wall_Type"].data.items()
                
                # for mesh_attribute in mesh_attributes:
                #     if mesh_attribute[0] == last_index:
                #         bpy.context.scene.attribute_wall_type = mesh_attribute[1].value
                
    #            for edge in sel_edges:
    #               index = edge.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == last_index:
                        bpy.context.scene.attribute_wall_type = mesh_attribute[1].value
                        
                bpy.ops.object.mode_set(mode='EDIT')
                
                print("new Number is", previous_last_index)
            # else:
            #     print("nessun cambio", len(selected_edges)) 
                
            # mesh_attributes = mesh.attributes["Wall_Type"].data.items()
            # print("mesh attributes", mesh_attributes)
            # bpy.context.scene.attribute_wall_type = len(selected_edges)
            # print("selezionati", len(selected_edges))
    except:
        pass
    
        

def update_attribute_wall_type(self, context):
    try:
        if context.area.type == 'VIEW_3D':
            bpy.ops.object.set_edge_attribute_as_wall_type()
    except:
        pass

classes = (
    OBJECT_OT_add_RoMa_Wall,
    VIEW3D_PT_RoMa_Wall,
    SetEdgeAttributeOperator
)

def register():
    bpy.types.VIEW3D_MT_mesh_add.append(add_RoMa_Wall_button)
    bpy.types.Scene.attribute_wall_type = bpy.props.FloatProperty(
                                        name="Type", 
                                        default=0,
                                        update = update_attribute_wall_type)
    
    bpy.app.handlers.depsgraph_update_post.append(callback_edge_selected)
    # bpy.utils.register_manual_map(add_RoMa_Wall_manual_map)
        
    for cls in classes:
        bpy.utils.register_class(cls)
        
def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(add_RoMa_Wall_button)
    del bpy.types.Scene.attribute_wall_type
    
    bpy.app.handlers.depsgraph_update_post.remove(callback_edge_selected)
    # bpy.utils.unregister_manual_map(add_RoMa_Wall_manual_map)
    
    for cls in classes:
        bpy.utils.unregister_class(cls)
     
    