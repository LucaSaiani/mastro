import bpy
#import bmesh 

from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import (
        AddObjectHelper,
        object_data_add
)
# from bpy.app.handlers import persistent
from mathutils import Vector
from bpy.props import StringProperty, IntProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel

previous_last_index = None

class OBJECT_OT_add_RoMa_facade(Operator, AddObjectHelper):
    """Create a new RoMa façade"""
    bl_idname = "mesh.add_roma_facade"
    bl_label = "RoMa Façade"
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

        
class VIEW3D_PT_RoMa_facade(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Façade"
    
    def draw(self, context):

        layout = self.layout
        obj = context.active_object
        scene = context.scene
        
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        layout.active = bool(context.active_object.mode=='EDIT')
        if "roma_facade_type_list" in scene:
            # col = layout.column()
            # subcol = col.column()
            # subcol.active = bool(context.active_object.mode=='EDIT')
            # subcol.prop(context.scene, "attribute_facade_type", text="Type:")
            layout.prop(context.scene, "roma_facade_type_name", text="Select Element")
            
            
            is_sortable = len(scene.roma_facade_type_list) > 1
            rows = 3
            if is_sortable:
                rows = 5
                
            row = layout.row()
            row.template_list("OBJECT_UL_Facade", "The_List", scene,
                            "roma_facade_type_list", scene, "roma_facade_type_index", rows = rows)
            # row.template_list("OBJECT_UL_Facade", "The_List", obj,
            #                    "roma_facade_type_list", obj, "roma_facade_type_index", rows = rows)
            
            col = row.column(align=True)
            col.operator("roma_facade_type_list.new_item", icon='ADD', text="")
            col.operator("roma_facade_type_list.delete_item", icon='REMOVE', text="")
            col.separator()
            col.operator("roma_facade_type_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("roma_facade_type_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
            
            #row = layout.row()
            #row.template_ID(obj, "active_material", new="material.new")
            
            # obj.mode = 'OBJECT'
            # obj.value = 0
            # obj.mode = 'EDIT'
            
            if obj.mode == 'EDIT':
                mesh = obj.data
                selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]

                # mesh_attributes = mesh.attributes["roma_facade_type"].data.items()

                
                # for edge in selected_edges:
                #     index = edge.index
                #     for mesh_attribute in mesh_attributes:
                #         if mesh_attribute[0] == index:
                #             # obj.mode = 'OBJECT'
                #             # obj.value = mesh_attribute[1]
                #             # obj.mode = 'EDIT'
                #             pass
                            
                row = layout.row()
                #print(scene.attribute_facade_type)
                #row.template_ID(scene, "roma_facade_type_list", new="material.new")
                row = layout.row(align=True)
                #row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.set_attribute_facade_type", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

            
            # if scene.roma_facade_type_index >= 0 and scene.roma_facade_type_list:
            if scene.roma_facade_type_index >= 0:
                item = scene.roma_facade_type_list[scene.roma_facade_type_index]
                row = layout.row()
                row.prop(item, "name")
                row.prop(item, "index")
            
        
        
        


class ListFacadeType(PropertyGroup):
    """Group of properties of the façade edges."""
    index: IntProperty(
           name="Index",
           description="Façade type index",
           default = 0)
    
    name: StringProperty(
           name="Name",
           description="The name of the façade segment",
           default="Façade")

    
    
class OBJECT_UL_Facade(UIList):
    """Façade type UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):

        # We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.3)
            # split.label(text="Index: %d" % (index))
            split.label(text=str(item.index)) 
            split.label(text=item.name, icon=custom_icon) 
            # layout.label(text=item.name, icon=custom_icon) 

            # layout.label(text=item.name, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)


class LIST_OT_NewItem(Operator):
    """Add a new item to the list"""

    bl_idname = "roma_facade_type_list.new_item"
    bl_label = "Add a new item"

    def execute(self, context):
        context.scene.roma_facade_type_list.add()
        #for el in bpy.context.scene.roma_facade_type_list:
            #print("pippo", bpy.context.scene.roma_facade_type_list[1].index)
           # print("pippo", el.index)
        #print("max", max(bpy.context.scene.roma_facade_type_list, key=lambda x: x.index))
        temp_list = []
        for el in bpy.context.scene.roma_facade_type_list:
            temp_list.append(el.index)
        print("max index = ", max(temp_list))
        last = len(bpy.context.scene.roma_facade_type_list)-1
        bpy.context.scene.roma_facade_type_list[last].index = max(temp_list)+1
        return{'FINISHED'}


class LIST_OT_DeleteItem(Operator):
    """Delete the selected item from the list."""

    bl_idname = "roma_facade_type_list.delete_item"
    bl_label = "Delete an item"

    @classmethod
    def poll(cls, context):
        return context.scene.roma_facade_type_list

    def execute(self, context):
        roma_facade_type_list = context.scene.roma_facade_type_list
        index = context.scene.roma_facade_type_index

        roma_facade_type_list.remove(index)
        context.scene.roma_facade_type_index = min(max(0, index - 1), len(roma_facade_type_list) - 1)

        return{'FINISHED'}
    
class LIST_OT_MoveItem(Operator):
    """Move an item in the list."""

    bl_idname = "roma_facade_type_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_facade_type_list

    def move_index(self):
        """ Move index of an item render queue while clamping it. """

        index = bpy.context.scene.roma_facade_type_index
        list_length = len(bpy.context.scene.roma_facade_type_list) - 1  # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_facade_type_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_facade_type_list = context.scene.roma_facade_type_list
        index = context.scene.roma_facade_type_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_facade_type_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
#class OPERATOR_update_RoMa_facade_attribute(bpy.types.Operator):
class OBJECT_OT_SetFacadeType(Operator):
    """Assign a façade type to the selected edge"""
    bl_idname = "object.set_attribute_facade_type"
    bl_label = "Assign a façade type to the selected edge"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # attribute_facade_type = context.scene.attribute_facade_type
        list_index = bpy.context.scene.roma_facade_type_index
        attribute_facade_type = bpy.context.scene.roma_facade_type_list[list_index].index
        
        # a custom attribute is assigned to the edges
        try:
            mesh.attributes["roma_facade_type"]
            # except:
            #     mesh.attributes.new(name="roma_facade_type", type="FLOAT", domain="EDGE")

            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')

            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]

            mesh_attributes = mesh.attributes["roma_facade_type"].data.items()

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
    mesh.attributes.new(name="roma_facade_type", type="INT", domain="EDGE")
    mesh.attributes.new(name="roma_plot_name", type="STRING", domain="FACE")
    
def add_RoMa_facade_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_RoMa_facade.bl_idname,
        text="RoMa Facade",
        icon='PLUGIN')
    

    
def update_attribute_facade_type(self, context):
    # try:
    #     if context.area.type == 'VIEW_3D':
    bpy.ops.object.set_attribute_facade_type()
    # except:
    #     pass
    
    



# per sapere quali segmenti sono selezionati

# import bmesh
# ob = bpy.context.object

# if ob.type != 'MESH':
#     raise TypeError("Active object is not a Mesh")

# me = ob.data

# if me.is_editmode:
#     # Gain direct access to the mesh
#     bm = bmesh.from_edit_mesh(me)
# else:
#     # Create a bmesh from mesh
#     # (won't affect mesh, unless explicitly written back)
#     bm = bmesh.new()
#     bm.from_mesh(me)

    
# # Get active face
# face = bm.faces.active

# selected = "selected"
# not_selected = " ".join(("NOT", selected))

# for edge in face.edges:
#     print("%12s - bm.edges[%i]" % ((selected if edge.select else not_selected), edge.index))