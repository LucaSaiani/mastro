import bpy
# import bmesh

from bpy.props import StringProperty, IntProperty, FloatProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel

import random
import decimal
from datetime import datetime

class VIEW3D_PT_RoMa_project_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "RoMa Project Data"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        pass


class VIEW3D_PT_RoMa_show_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "Show Data"
    bl_parent_id = "VIEW3D_PT_RoMa_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        self.layout.prop(context.window_manager, "toggle_show_data", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        layout.active = context.window_manager.toggle_show_data
        
        # flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        # col = flow.column()
        # col = flow.column(heading="Mass", align = True)
        col = layout.column(heading="Mass", align=True)
        col.prop(context.window_manager, 'toggle_plot_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_block_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_use_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_storey_number', icon_only=False)
        # col.separator()
        col = layout.column(heading="Façade", align = True)
        col.prop(context.window_manager, 'toggle_facade_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_facade_normal', icon_only=False)
        # col.separator()
        col = layout.column(heading="Floor", align = True)
        col.prop(context.window_manager, 'toggle_floor_name', icon_only=False)
        
############################      ############################
############################ MASS ############################
############################      ############################
           
class VIEW3D_PT_RoMa_mass_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "Mass Data"
    bl_parent_id = "VIEW3D_PT_RoMa_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    def draw(self, context):
        pass
      
############################        ############################
############################ PLOT   ############################
############################        ############################ 
            
class VIEW3D_PT_RoMa_mass_plot_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Plot"
    bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        # row.label(text="Plot")
        
        rows = 3
        
        row = layout.row()
        row.template_list("OBJECT_UL_Plot", "plot_list", scene,
                        "roma_plot_name_list", scene, "roma_plot_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_plot_name_list.new_item", icon='ADD', text="")
        # col.operator("roma_facade_type_list.delete_item", icon='REMOVE', text="")
        col.separator()
        col.operator("roma_plot_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_plot_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        # row.prop(context.scene, "roma_plot_names", icon="MOD_BOOLEAN", icon_only=True, text="")
        # row.operator("scene.add_plot_name", icon="ADD", text="New")
        
        if scene.roma_plot_name_list_index >= 0 and scene.roma_plot_name_list:
            item = scene.roma_plot_name_list[scene.roma_plot_name_list_index]
            row.prop(item, "name", icon_only=True)
        # row.prop(item, "index")
        
class OBJECT_UL_Plot(UIList):
   
    """Façade type UIList."""
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        # We could write some code to decide which icon to use here...
        custom_icon = 'MOD_BOOLEAN'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            
            # split.label(text="Index: %d" % (index))
            
            split = layout.split(factor=0.3)
            split.label(text="Id: %d" % (item.id)) 
            split.label(text=item.name, icon=custom_icon) 
            
            # layout.alignment = 'LEFT'
            # layout.label(text=item.name, icon="MOD_BOOLEAN")
            
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

        # self.filter_zero_id(context, data, "roma_plot_name_list")


    def filter_items(self, context, data, propname):
        """Filter and order items in the list."""

        # We initialize filtered and ordered as empty lists. Notice that 
        # if all sorting and filtering is disabled, we will return
        # these empty. 

        filtered = []
        ordered = []
        items = getattr(data, propname)
        # Initialize with all items visible
        filtered = [self.bitflag_filter_item] * len(items)
        
        for i, item in enumerate(items):
            if item.id == 0:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class PLOT_LIST_OT_NewItem(Operator):
    bl_idname = "roma_plot_name_list.new_item"
    bl_label = "Add a new plot"

    def execute(self, context): 
        context.scene.roma_plot_name_list.add()
        # last = len(context.scene.roma_plot_name_list)-1
        # if last == 0:
        #     context.scene.roma_plot_name_list[0].id = 0
        #     context.scene.roma_plot_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_plot_name_list[0].RND = rndNumber
        #     context.scene.roma_plot_name_list.add()
        temp_list = []    
        for el in context.scene.roma_plot_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_plot_name_list)-1
        
        context.scene.roma_plot_name_list[last].id = max(temp_list)+1
        rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        context.scene.roma_plot_name_list[last].RND = rndNumber
            
        return{'FINISHED'}
    
class PLOT_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_plot_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_plot_name_list

    def move_index(self):
        index = bpy.context.scene.roma_plot_name_list_index
        list_length = len(bpy.context.scene.roma_plot_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_plot_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_plot_name_list = context.scene.roma_plot_name_list
        index = context.scene.roma_plot_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_plot_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class plot_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Plot name id",
           default = 0)
    
    name: StringProperty(
           name="Plot Name",
           description="The name of the plot",
           default="")
    
    RND: FloatProperty(
           name="Random Value per Plot",
           description="A random value assigned to each plot",
           default = 0)
        
############################        ############################
############################ BLOCK  ############################
############################        ############################

    
class VIEW3D_PT_RoMa_mass_block_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Block"
    bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        
        #row.label(text="Block")
        # row.prop(context.window_manager, 'toggle_block_name', toggle=True, icon="HIDE_OFF", icon_only=True)
        
        # is_sortable = len(scene.roma_block_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Block", "block_list", scene,
                        "roma_block_name_list", scene, "roma_block_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_block_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_block_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_block_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        if scene.roma_block_name_list_index >= 0 and scene.roma_block_name_list:
            item = scene.roma_block_name_list[scene.roma_block_name_list_index]
            row.prop(item, "name", icon_only=True)
            
class OBJECT_UL_Block(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'HOME'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.3)
            split.label(text="Id: %d" % (item.id)) 
            split.label(text=item.name, icon=custom_icon) 
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        for i, item in enumerate(items):
            if item.id == 0:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class BLOCK_LIST_OT_NewItem(Operator):
    bl_idname = "roma_block_name_list.new_item"
    bl_label = "Add a new block"

    def execute(self, context): 
        context.scene.roma_block_name_list.add()
        # last = len(context.scene.roma_block_name_list)-1
        # if last == 0:
        #     context.scene.roma_block_name_list[0].id = 0
        #     context.scene.roma_block_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_block_name_list[0].RND = rndNumber
        #     context.scene.roma_block_name_list.add()
        temp_list = []    
        for el in context.scene.roma_block_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_block_name_list)-1
        
        context.scene.roma_block_name_list[last].id = max(temp_list)+1
        rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        context.scene.roma_block_name_list[last].RND = rndNumber
            
        return{'FINISHED'}
    
class BLOCK_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_block_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_block_name_list

    def move_index(self):
        index = bpy.context.scene.roma_block_name_list_index
        list_length = len(bpy.context.scene.roma_block_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_block_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_block_name_list = context.scene.roma_block_name_list
        index = context.scene.roma_block_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_block_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class block_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Block name id",
           default = 0)
    
    name: StringProperty(
           name="Block Name",
           description="The name of the block",
           default="")
    
    RND: FloatProperty(
           name="Random Value per Block",
           description="A random value assigned to each block",
           default = 0)
            
############################        ############################
############################ USE    ############################
############################        ############################

class VIEW3D_PT_RoMa_mass_use_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Use"
    bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        #row.label(text="Use")
        # row.prop(context.window_manager, 'toggle_use_name', toggle=True, icon="HIDE_OFF", icon_only=True)
        
        # is_sortable = len(scene.roma_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Use", "use_list", scene,
                        "roma_use_name_list", scene, "roma_use_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_use_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_use_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_use_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        if scene.roma_use_name_list_index >= 0 and scene.roma_use_name_list:
            item = scene.roma_use_name_list[scene.roma_use_name_list_index]
            row.prop(item, "name", icon_only=True)
            
class OBJECT_UL_Use(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'COMMUNITY'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.3)
            split.label(text="Id: %d" % (item.id)) 
            split.label(text=item.name, icon=custom_icon) 
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        for i, item in enumerate(items):
            if item.id == 0:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class USE_LIST_OT_NewItem(Operator):
    bl_idname = "roma_use_name_list.new_item"
    bl_label = "Add a new use"

    def execute(self, context): 
        context.scene.roma_use_name_list.add()
        # last = len(context.scene.roma_use_name_list)-1
        # if last == 0:
        #     context.scene.roma_use_name_list[0].id = 0
        #     context.scene.roma_use_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_use_name_list[0].RND = rndNumber
        #     context.scene.roma_use_name_list.add()
        temp_list = []    
        for el in context.scene.roma_use_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_use_name_list)-1
        
        context.scene.roma_use_name_list[last].id = max(temp_list)+1
        rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        context.scene.roma_use_name_list[last].RND = rndNumber
            
        return{'FINISHED'}
    
class USE_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_use_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_use_name_list

    def move_index(self):
        index = bpy.context.scene.roma_use_name_list_index
        list_length = len(bpy.context.scene.roma_use_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_use_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_use_name_list = context.scene.roma_use_name_list
        index = context.scene.roma_use_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_use_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class use_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Use name id",
           default = 0)
    
    name: StringProperty(
           name="Use Name",
           description="The use of the block",
           default="")
    
    RND: FloatProperty(
           name="Random Value per Use",
           description="A random value assigned to each use",
           default = 0)
    
############################            ############################
############################ TYPOLOGY   ############################
############################            ############################

class VIEW3D_PT_RoMa_mass_typology_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Typology"
    bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        rows = 3
        row = layout.row()
        row.template_list("OBJECT_UL_Typology", "typology_list", scene,
                        "roma_typology_name_list", scene, "roma_typology_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_typology_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_typology_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_typology_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        if scene.roma_typology_name_list_index >= 0 and scene.roma_typology_name_list:
            item = scene.roma_typology_name_list[scene.roma_typology_name_list_index]
            row.prop(item, "name", icon_only=True)
            
class OBJECT_UL_Typology(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'ASSET_MANAGER'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.3)
            split.label(text="Id: %d" % (item.id)) 
            split.label(text=item.name, icon=custom_icon) 
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        for i, item in enumerate(items):
            if item.id == 0:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class TYPOLOGY_LIST_OT_NewItem(Operator):
    bl_idname = "roma_typology_name_list.new_item"
    bl_label = "Add a new typology"

    def execute(self, context): 
        context.scene.roma_typology_name_list.add()
        # last = len(context.scene.roma_use_name_list)-1
        # if last == 0:
        #     context.scene.roma_use_name_list[0].id = 0
        #     context.scene.roma_use_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_use_name_list[0].RND = rndNumber
        #     context.scene.roma_use_name_list.add()
        temp_list = []    
        for el in context.scene.roma_typology_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_typology_name_list)-1
        
        context.scene.roma_typology_name_list[last].id = max(temp_list)+1
        rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        context.scene.roma_typology_name_list[last].RND = rndNumber
            
        return{'FINISHED'}
    
class TYPOLOGY_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_typology_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_typology_name_list

    def move_index(self):
        index = bpy.context.scene.roma_typology_name_list_index
        list_length = len(bpy.context.scene.roma_typology_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_typology_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_use_name_list = context.scene.roma_typology_name_list
        index = context.scene.roma_typology_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_use_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class typology_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Typology name id",
           default = 0)
    
    name: StringProperty(
           name="Typology Name",
           description="The typology of the block",
           default="")
    
    RND: FloatProperty(
           name="Random Value per Typology",
           description="A random value assigned to each typology",
           default = 0)
    
############################            ############################
############################ BUILDING   ############################
############################            ############################
        
        
class VIEW3D_PT_RoMa_building_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "Building Data"
    bl_parent_id = "VIEW3D_PT_RoMa_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        pass
        
############################        ############################
############################ FACADE ############################
############################        ############################
        
class VIEW3D_PT_RoMa_building_facade_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Façade"
    bl_parent_id = "VIEW3D_PT_RoMa_building_data"
    bl_options = {'DEFAULT_CLOSED'}      
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.  
        
        row = layout.row()
       # row.label(text="Façade")
        
        # is_sortable = len(scene.roma_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Facade", "facade_list", scene,
                        "roma_facade_name_list", scene, "roma_facade_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_facade_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_facade_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_facade_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        if scene.roma_facade_name_list_index >= 0 and scene.roma_facade_name_list:
            item = scene.roma_facade_name_list[scene.roma_facade_name_list_index]
            row.prop(item, "name", icon_only=True)
            
class OBJECT_UL_Facade(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'NODE_TEXTURE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.3)
            split.label(text="Id: %d" % (item.id)) 
            split.label(text=item.name, icon=custom_icon) 
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        for i, item in enumerate(items):
            if item.id == 0:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class FACADE_LIST_OT_NewItem(Operator):
    bl_idname = "roma_facade_name_list.new_item"
    bl_label = "Add a new façade type"

    def execute(self, context): 
        context.scene.roma_facade_name_list.add()
        # last = len(context.scene.roma_use_name_list)-1
        # if last == 0:
        #     context.scene.roma_use_name_list[0].id = 0
        #     context.scene.roma_use_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_use_name_list[0].RND = rndNumber
        #     context.scene.roma_use_name_list.add()
        temp_list = []    
        for el in context.scene.roma_facade_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_facade_name_list)-1
        
        context.scene.roma_facade_name_list[last].id = max(temp_list)+1
        # rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        # context.scene.roma_use_name_list[last].RND = rndNumber
            
        return{'FINISHED'}
    
class FACADE_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_facade_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_facade_name_list

    def move_index(self):
        index = bpy.context.scene.roma_facade_name_list_index
        list_length = len(bpy.context.scene.roma_facade_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_facade_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_facade_name_list = context.scene.roma_facade_name_list
        index = context.scene.roma_facade_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_facade_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class facade_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Façade name id",
           default = 0)
    
    name: StringProperty(
           name="Façade Name",
           description="The name of the façade",
           default="")
    
    normal: IntProperty(
           name="Façade Normal",
           description="Invert the normal of the façade",
           default = 1)
    
############################        ############################
############################ FLOOR  ############################
############################        ############################
            

class VIEW3D_PT_RoMa_building_floor_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Floor"
    bl_parent_id = "VIEW3D_PT_RoMa_building_data"
    bl_options = {'DEFAULT_CLOSED'}      
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        #row.label(text="Floor")
        
        # is_sortable = len(scene.roma_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Floor", "floor_list", scene,
                        "roma_floor_name_list", scene, "roma_floor_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_floor_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_floor_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_floor_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        if scene.roma_floor_name_list_index >= 0 and scene.roma_floor_name_list:
            item = scene.roma_floor_name_list[scene.roma_floor_name_list_index]
            row.prop(item, "name", icon_only=True)
          
class OBJECT_UL_Floor(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'VIEW_PERSPECTIVE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.3)
            split.label(text="Id: %d" % (item.id)) 
            split.label(text=item.name, icon=custom_icon) 
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        for i, item in enumerate(items):
            if item.id == 0:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class FLOOR_LIST_OT_NewItem(Operator):
    bl_idname = "roma_floor_name_list.new_item"
    bl_label = "Add a new floor type"

    def execute(self, context): 
        context.scene.roma_floor_name_list.add()
        temp_list = []    
        for el in context.scene.roma_floor_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_floor_name_list)-1
        
        context.scene.roma_floor_name_list[last].id = max(temp_list)+1
            
        return{'FINISHED'}
    
class FLOOR_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_floor_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_floor_name_list

    def move_index(self):
        index = bpy.context.scene.roma_floor_name_list_index
        list_length = len(bpy.context.scene.roma_floor_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_floor_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_floor_name_list = context.scene.roma_floor_name_list
        index = context.scene.roma_floor_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_floor_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class floor_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Floor name id",
           default = 0)
    
    name: StringProperty(
           name="Floor Name",
           description="The name of the floor",
           default="")
    
    # normal: IntProperty(
    #        name="Façade Normal",
    #        description="Invert the normal of the façade",
    #        default = 0) 
        


##############################              #############################
############################## other stuff  #############################
##############################              #############################
class name_with_id(PropertyGroup):
    id: IntProperty(
        name="Id",
        description="Name id",
        default = 0)
    
    name: StringProperty(
        name="Name",
        description="Name",
        default = "")
        

# def update_plot_name_toggle(self, context):
#     if self.plot_name_toggle:
#         bpy.ops.plot_name_OT('INVOKE_DEFAULT')
#     return



############################## modal operator #############################
# class TEST_OT_modal_operator(Operator):
#     bl_idname = "test.modal"
#     bl_label = "Demo modal operator"

#     def modal(self, context, event):
#         if not context.window_manager.test_toggle:
#             context.window_manager.event_timer_remove(self._timer)
#             print("done")
#             return {'FINISHED'}
#         print("pass through")
#         return {'PASS_THROUGH'}

#     def invoke(self, context, event):
#         self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
#         context.window_manager.modal_handler_add(self)
#         print("modal")
#         return {'RUNNING_MODAL'}



