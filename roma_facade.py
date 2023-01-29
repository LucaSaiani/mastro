import bpy
import bmesh 

from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import (
        AddObjectHelper,
        object_data_add
)
# from bpy.app.handlers import persistent
from mathutils import Vector
from bpy.props import StringProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel

previous_last_index = None

class OBJECT_OT_add_RoMa_facade(Operator, AddObjectHelper):
    """Create a new RoMa facade"""
    bl_idname = "mesh.add_roma_facade"
    bl_label = "Add RoMa facade"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):

        add_RoMa_facade(self, context)
        return {'FINISHED'}
    
class SetEdgeAttributeOperator_facade_type(bpy.types.Operator):
    """Set Edge Attribute as facade Type"""
    bl_idname = "object.set_attribute_facade_type"
    bl_label = "Set Edge Attribute as facade Type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_facade_type = context.scene.attribute_facade_type
        
        # a custom attribute is assigned to the edges
        try:
            mesh.attributes["facade_Type"]
            # except:
            #     mesh.attributes.new(name="facade_Type", type="FLOAT", domain="EDGE")

            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')

            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]

            mesh_attributes = mesh.attributes["facade_Type"].data.items()

            for edge in selected_edges:
                index = edge.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_facade_type

            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to edge "+str(attribute_facade_type))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class VIEW3D_PT_RoMa_facade(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Facade"
    
    def draw(self, context):
        
        layout = self.layout
        scene = context.scene
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        col = layout.column()
        subcol = col.column()
        subcol.active = bool(context.active_object.mode=='EDIT')
        subcol.prop(context.scene, "attribute_facade_type", text="Type")
        
        # col = layout.column()
        # subcol = col.column()
        # subcol.label(text="List of Values:")
        # subcol.template_list("UI_UL_list", "my_list", context.scene, "my_list", context.scene, "my_list_index")
        
        
        rows = 2
        row = layout.row()
        row.template_list("MY_UL_List", "The_List", scene,
                           "my_list", scene, "list_index")
        
        col = row.column(align=True)
        col.operator("my_list.new_item", icon='ADD', text="")
        col.operator("my_list.delete_item", icon='REMOVE', text="")
        col.separator()
        col.operator("my_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("my_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'

        
        # row = layout.row()
        # row.template_list("MY_UL_List", "The_List", scene,
        #                   "my_list", scene, "list_index")

        # row = layout.row()
        # row.operator('my_list.new_item', text='NEW')
        # row.operator('my_list.delete_item', text='REMOVE')
        # row.operator('my_list.move_item', text='UP').direction = 'UP'
        # row.operator('my_list.move_item', text='DOWN').direction = 'DOWN'

        if scene.list_index >= 0 and scene.my_list:
            item = scene.my_list[scene.list_index]

            row = layout.row()
            row.prop(item, "name")
            row.prop(item, "random_prop")
        

        # row = layout.row()
        # row.prop(context.scene, "attribute_facade_type", text="Type")
        # if context.active_object.mode=='EDIT':
        #     row.enabled = True
        # else:
        #     row.enabled = False
        
# class OPERATOR_update_RoMa_facade_attribute(bpy.types.Operator):
#     """Update value of RoMa facade type when an edge is selected"""
#     bl_idname = "object.update_roma_facade_type"
#     bl_label = "Update RoMa facade type attribute"
#     bl_options = {'REGISTER', 'UNDO'}
    
    
#     def execute(self, context):
#         # global previous_last_index
#         # obj = bpy.context.active_object
#         # try:
#         #     mesh = obj.data
#         #     mesh.attributes["facade_Type"]
#         #     if obj.mode == 'EDIT':
#         #         # Get the bmesh data
#         #         bm = bmesh.from_edit_mesh(obj.data)

#         #         selected_edges = []
#         #         for edge in bm.edges:
#         #             if edge.select:
#         #                 selected_edges.append(edge)
#         #                 last_index = edge.index
#         #         if previous_last_index == None or previous_last_index != last_index:
#         #             previous_last_index = last_index
                        
#         #             bpy.ops.object.mode_set(mode='OBJECT')
#         #             mesh = obj.data
#         #             sel_edges = [e for e in bpy.context.active_object.data.edges if e.select]
#         #             mesh_attributes = mesh.attributes["facade_Type"].data.items()
                    
#         #             index = edge.index
#         #             for mesh_attribute in mesh_attributes:
#         #                 if mesh_attribute[0] == last_index:
#         #                     bpy.context.scene.attribute_facade_type = mesh_attribute[1].value
                            
#         #             bpy.ops.object.mode_set(mode='EDIT')
#         # except:
#         #     pass
#         return {'FINISHED'}

class ListItem(PropertyGroup):
    """Group of properties representing an item in the list."""

    name: StringProperty(
           name="Name",
           description="A name for this item",
           default="Untitled")

    random_prop: StringProperty(
           name="Any other property you want",
           description="",
           default="")
    
class MY_UL_List(UIList):
    """Demo UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        # We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)


class LIST_OT_NewItem(Operator):
    """Add a new item to the list."""

    bl_idname = "my_list.new_item"
    bl_label = "Add a new item"

    def execute(self, context):
        context.scene.my_list.add()

        return{'FINISHED'}


class LIST_OT_DeleteItem(Operator):
    """Delete the selected item from the list."""

    bl_idname = "my_list.delete_item"
    bl_label = "Deletes an item"

    @classmethod
    def poll(cls, context):
        return context.scene.my_list

    def execute(self, context):
        my_list = context.scene.my_list
        index = context.scene.list_index

        my_list.remove(index)
        context.scene.list_index = min(max(0, index - 1), len(my_list) - 1)

        return{'FINISHED'}
    
class LIST_OT_MoveItem(Operator):
    """Move an item in the list."""

    bl_idname = "my_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.my_list

    def move_index(self):
        """ Move index of an item render queue while clamping it. """

        index = bpy.context.scene.list_index
        list_length = len(bpy.context.scene.my_list) - 1  # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        my_list = context.scene.my_list
        index = context.scene.list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        my_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
def add_RoMa_facade(self, context):
    scale_x = self.scale.x
    # scale_y = self.scale.y

    verts = [
        Vector((0, 0, 0)),
        Vector((10 * scale_x, 0, 0))
    ]

    edges = [[0,1]]
    faces = []

    mesh = bpy.data.meshes.new(name="RoMa facade")
    mesh.from_pydata(verts, edges, faces)
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)
    mesh.attributes.new(name="facade_Type", type="INT", domain="EDGE")
    
def add_RoMa_facade_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_RoMa_facade.bl_idname,
        text="Add RoMa facade",
        icon='PLUGIN')
    
def callback_edge_selected(context):
    global previous_last_index
    
    obj = bpy.context.active_object
    try:
        mesh = obj.data
        mesh.attributes["facade_Type"]
        if obj.mode == 'EDIT':
            # Get the bmesh data
            bm = bmesh.from_edit_mesh(obj.data)

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
                mesh_attributes = mesh.attributes["facade_Type"].data.items()
                
                index = edge.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == last_index:
                        bpy.context.scene.attribute_facade_type = mesh_attribute[1].value
                        
                bpy.ops.object.mode_set(mode='EDIT')
                
       
    except:
        pass
    
def update_attribute_facade_type(self, context):
    try:
        if context.area.type == 'VIEW_3D':
            bpy.ops.object.set_attribute_facade_type()
    except:
        pass
    
    
    