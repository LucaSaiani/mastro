# Copyright (C) 2022-2025 Luca Saiani

# luca.saiani@gmail.com

# Created by Luca Saiani
# This is part of MaStro addon for Blender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

from bpy.props import StringProperty, IntProperty
from bpy.types import Operator, Panel, UIList, PropertyGroup

import math

class VIEW3D_PT_MaStro_Mass(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Mass"
    #bl_idname = "MASTRO_PT_Mass"
    
    
    # global blockName
    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    @classmethod
    def poll(cls, context):
        return  (context.object is not None and 
                # context.selected_objects != [] and
                context.object.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro mass" in context.object.data)
    
    def draw(self, context):
        # obj = context.active_object 
        obj = context.object
        if obj is not None and obj.type == "MESH":
        
            mode = obj.mode
            if mode == "OBJECT":
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                # row = layout.row()
                row = layout.row(align=True)
                
                # layout.prop(obj.mastro_props, "mastro_option_attribute", text="Option")
                # layout.prop(obj.mastro_props, "mastro_phase_attribute", text="Phase")
                # row = layout.row()
                # row = layout.row(align=True)
                row.prop(context.scene, "mastro_block_names", icon="MOD_BOOLEAN", icon_only=True, text="Block")
                if scene.mastro_block_name_list and len(scene.mastro_block_name_list) >0:
                    row.label(text = scene.mastro_block_name_current[0].name)
                row = layout.row(align=True)
                row.prop(context.scene, "mastro_building_names", icon="HOME", icon_only=True, text="Building")
                if scene.mastro_building_name_list and len(scene.mastro_building_name_list) >0:
                    row.label(text = scene.mastro_building_name_current[0].name)
                
                    
            elif mode == "EDIT":      
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
                    layout.enabled = True
                else:
                    layout.enabled = False
                # col = layout.column()
                # subcol = col.column()
                
                # layout.active = bool(context.active_object.mode=='EDIT')
                # row = layout.row()
                
         
                ################ TYPOLOGY ######################
                row = layout.row(align=True)
                
                # disable the number of storeys if there are no liquids
                # current_typology = scene.mastro_typology_name_current[0]
                
                
                # since it is possible to sort typologies in the ui, it can be that the index of the element
                # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
                # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
                item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == scene.mastro_typology_name_current[0].id)
                use_list = item.useList
                uses = use_list.split(";")
                tmp_enabled = False
                for useID in uses:
                    if context.scene.mastro_use_name_list[int(useID)].liquid == True:
                        tmp_enabled = True
                        break
                row.prop(context.scene, "attribute_mass_storeys", text="N° of storeys") 
                row.enabled = tmp_enabled
                
                row = layout.row(align=True)
                row.prop(context.scene, "mastro_typology_names", icon="ASSET_MANAGER", icon_only=True, text="Typology")
                if len(scene.mastro_typology_name_list) >0:
                    row.label(text=scene.mastro_typology_name_current[0].name)
                rows = 3
                row = layout.row()
                row.template_list("OBJECT_UL_OBJ_Typology_Uses", 
                                  "obj_typology_uses_list", 
                                  scene,
                                  "mastro_obj_typology_uses_name_list",
                                  scene,
                                  "mastro_obj_typology_uses_name_list_index",
                                  rows = rows)
                
      

class OBJECT_UL_OBJ_Typology_Uses(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'COMMUNITY'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.5)
            split.label(text="Storeys: %s" % (item.storeys))
            split.label(text=item.name)
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
    
class VIEW3D_PT_MaStro_Block(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Block"
    
    @classmethod
    def poll(cls, context):
        return  (context.object is not None and 
                context.object.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro block" in context.object.data)
    
    def draw(self, context):
        obj = context.object
        if obj is not None and obj.type == "MESH":
        
            mode = obj.mode
            if mode == "OBJECT":
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                row = layout.row(align=True)
                
                row.prop(context.scene, "mastro_block_names", icon="MOD_BOOLEAN", icon_only=True, text="Block")
                if scene.mastro_block_name_list and len(scene.mastro_block_name_list) >0:
                    row.label(text = scene.mastro_block_name_current[0].name)
                # row = layout.row(align=True)
                # row.prop(context.scene, "mastro_building_names", icon="HOME", icon_only=True, text="Building")
                # if scene.mastro_building_name_list and len(scene.mastro_building_name_list) >0:
                #     row.label(text = scene.mastro_building_name_current[0].name)
                
                    
            elif mode == "EDIT":      
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False

                layout_1 = layout.column()
                layout_0 = layout.column()
               
                # layout_0 = self.layout
                # layout_0.use_property_split = True    
                # layout_0.use_property_decorate = False  # No animation. 
                # layout_1 = self.layout
                # layout_1.use_property_split = True    
                # layout_1.use_property_decorate = False  # No animation.
               
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[0] == True: #we are selecting edges
                    layout_0.enabled = True
                else:
                    layout_0.enabled = False
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    layout_1.enabled = True
                else:
                    layout_1.enabled = False
                
                
         
                ################ TYPOLOGY ######################
                row = layout_1.row(align=True)
                row.prop(context.scene, "attribute_mass_storeys", text="N° of storeys") 
                row = layout_1.row(align=True)
                row.prop(context.scene, "attribute_block_depth", text="Depth") 
                # disable the number of storeys if there are no liquids
                # current_typology = scene.mastro_typology_name_current[0]
                
                
                # since it is possible to sort typologies in the ui, it can be that the index of the element
                # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
                # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
                row = layout_1.row(align=True)
                item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == scene.mastro_typology_name_current[0].id)
                use_list = item.useList
                uses = use_list.split(";")
                tmp_enabled = False
                for useID in uses:
                    if context.scene.mastro_use_name_list[int(useID)].liquid == True:
                        tmp_enabled = True
                        break
                
                row.enabled = tmp_enabled
                
                row = layout_1.row(align=True)
                row.prop(context.scene, "mastro_typology_names", icon="ASSET_MANAGER", icon_only=True, text="Typology")
                if len(scene.mastro_typology_name_list) >0:
                    row.label(text=scene.mastro_typology_name_current[0].name)
                rows = 3
                row = layout_1.row()
                row.template_list("OBJECT_UL_OBJ_Typology_Uses", 
                                  "obj_typology_uses_list", 
                                  scene,
                                  "mastro_obj_typology_uses_name_list",
                                  scene,
                                  "mastro_obj_typology_uses_name_list_index",
                                  rows = rows)
                
                row = layout_1.row(align=True)
                row.prop(context.scene, "attribute_block_normal", text="Invert Normal") 
                
                row = layout_0.row(align=True)
                row.prop(context.scene, "attribute_block_side_angle", text="Side rotation") 
    
    
# class OBJECT_OT_SetTypologyId(Operator):
#     """Set Face Attribute as typology of the building"""
#     bl_idname = "object.set_attribute_mass_typology_id"
#     bl_label = "Set Face Attribute as Typology of the Building"
#     bl_options = {'REGISTER', 'UNDO'}
    
#     def execute(self, context):
        
        # obj = context.active_object
        # mesh = obj.data

        # # attribute_mass_typology_id = context.scene.attribute_mass_typology_id
        
        # try:
        #     mesh.attributes["mastro_typology_id"]
        #     # attribute_mass_typology_id = context.scene.attribute_mass_typology_id

        #     mode = obj.mode
        #     bpy.ops.object.mode_set(mode='OBJECT')
           
        #     selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
        #     mesh_attributes = mesh.attributes["mastro_typology_id"].data.items()

            
        #     for face in selected_faces:
        #         index = face.index
        #         for mesh_attribute in mesh_attributes:
        #             if mesh_attribute[0] == index:
        #                 mesh_attribute[1].value = context.scene.attribute_mass_typology_id
        #                 break
               
           
        #     bpy.ops.object.mode_set(mode=mode)
                    
        #     # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
        #     return {'FINISHED'}
        # except:
        #     return {'FINISHED'}
        

'''Set the number of storeys of the selected face attribute of the MaStro mesh'''
class OBJECT_OT_Set_Face_Attribute_Storeys(Operator):
    bl_idname = "object.set_mesh_face_attribute_storeys"
    bl_label = "Set face attributes assigned to the MaStro mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        # mesh.attributes["mastro_number_of_storeys"]
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_faces = [p for p in context.active_object.data.polygons if p.select]
        for face in selected_faces:
            faceIndex = face.index
            data = update_mesh_face_attributes_storeys(context, mesh, faceIndex)
            mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value = data["numberOfStoreys"]
            mesh.attributes["mastro_list_storey_A"].data[faceIndex].value = data["storey_list_A"]
            mesh.attributes["mastro_list_storey_B"].data[faceIndex].value = data["storey_list_B"]
        bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}

        
'''Mass: function to update number of storeys accordingly to the assigned number of storeys'''
def update_mesh_face_attributes_storeys(context, mesh, faceIndex, storeysSet = None):
    typology_id = mesh.attributes["mastro_typology_id"].data[faceIndex].value
    projectUses = context.scene.mastro_use_name_list
    # if the function is run once the user updates the number of storeys,
    # the number of storeys is read from context.scene.attribute_mass_storeys.
    # Else the function is run because the user is updating the typology list and
    # in this case the number of storeys used is the one stored in each face of the mesh
    if storeysSet == None:
        numberOfStoreys = context.scene.attribute_mass_storeys
    else:
        numberOfStoreys = storeysSet
    # since it is possible to sort typologies in the ui, it can be that the index of the element
    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    item = next(i for i in context.scene.mastro_typology_name_list if i["id"] == typology_id)
    use_list = item.useList
    # uses are listed top to bottom, but they need to
    # be added bottom to top           
    useSplit = use_list.split(";")            
    useSplit.reverse() 
    
    storey_list_A = "1"
    storey_list_B = "1"
    liquidPosition = [] # to count how many liquid uses they are
    fixedStoreys = 0 # to count how many fixed storeys they are

    
    for enum, el in enumerate(useSplit):
        ###setting the values for each use
        for use in projectUses:
            
            if use.id == int(el):
                # number of storeys for the use
                # if a use is "liquid" the number of storeys is set as 00
                if use.liquid: 
                    storeys = "00"
                    liquidPosition.append(enum)
                else:
                    fixedStoreys += use.storeys
                    storeys = str(use.storeys)
                    if use.storeys < 10:
                        storeys = "0" + storeys
                        
                storey_list_A += storeys[0]
                storey_list_B += storeys[1]
                break

    # liquid storeys need to be converted to actual storeys
    storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
    # if the typology has more storeys than the selected mass
    # some extra storeys are added
    if storeyCheck < 1: 
        numberOfStoreys = fixedStoreys + len(liquidPosition)
    storeyLeft = numberOfStoreys - fixedStoreys

    if len(liquidPosition) > 0:
        # the 1 at the start of the number is removed
        storey_list_A = storey_list_A[1:]
        storey_list_B = storey_list_B[1:]
        
        n = storeyLeft/len(liquidPosition)
        liquidStoreyNumber = math.floor(n)

        insert = str(liquidStoreyNumber)
        if liquidStoreyNumber < 10:
            insert = "0" + insert
            
        index = 0
        while index < len(liquidPosition):
            el = liquidPosition[index]
            # if the rounding of the liquid storeys is uneven,
            # the last liquid floor is increased of 1 storey
            if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
                insert = str(liquidStoreyNumber +1) 
                if liquidStoreyNumber +1 < 10:
                    insert = "0" + insert
                
            storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
            storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
            index += 1
        # the 1 is re-added  
        storey_list_A = "1" + storey_list_A
        storey_list_B = "1" + storey_list_B

    data = {"numberOfStoreys" : int(numberOfStoreys),
            "storey_list_A" : int(storey_list_A),
            "storey_list_B" : int(storey_list_B)
            }
    return data

'''Set the number of storeys of the selected edfe attribute of the MaStro block'''
class OBJECT_OT_Set_Edge_Attribute_Storeys(Operator):
    bl_idname = "object.set_mesh_edge_attribute_storeys"
    bl_label = "Set edge storey attributes assigned to the MaStro block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        # mesh.attributes["mastro_number_of_storeys"]
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_edges = [e for e in context.active_object.data.edges if e.select]
        
        for edge in selected_edges:
            edgeIndex = edge.index
            data = update_mesh_edge_attributes_storeys(context, mesh, edgeIndex)
            mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value = data["numberOfStoreys"]
            mesh.attributes["mastro_list_storey_A_EDGE"].data[edgeIndex].value = data["storey_list_A"]
            mesh.attributes["mastro_list_storey_B_EDGE"].data[edgeIndex].value = data["storey_list_B"]
        # else:
        #     active_vert = bpy.context.scene.previous_selection_vert_id
        #     active_edges =  [e for e in mesh.edges if active_vert in e.vertices]
        #     for edge in active_edges:
        #         edgeIndex = edge.index
        #         data = update_mesh_edge_attributes_storeys(context, mesh, edgeIndex)
        #         mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value = data["numberOfStoreys"]
        #         mesh.attributes["mastro_list_storey_A_EDGE"].data[edgeIndex].value = data["storey_list_A"]
        #         mesh.attributes["mastro_list_storey_B_EDGE"].data[edgeIndex].value = data["storey_list_B"]
        bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}
    
'''Block: function to update number of storeys accordingly to the assigned number of storeys'''
def update_mesh_edge_attributes_storeys(context, mesh, edgeIndex, storeysSet = None):
    # in case the edge is a new edge, the tipology id doesn't exist so the one set in the UI is used instead
    if len(mesh.attributes["mastro_typology_id_EDGE"].data) > 0:
        typology_id = mesh.attributes["mastro_typology_id_EDGE"].data[edgeIndex].value
    else:
        typology_id = context.scene.mastro_typology_name_current[0].id
    projectUses = context.scene.mastro_use_name_list
    # if the function is run once the user updates the number of storeys,
    # the number of storeys is read from context.scene.attribute_mass_storeys.
    # Else the function is run because the user is updating the typology list and
    # in this case the number of storeys used is the one stored in each edge of the mesh
    if storeysSet == None:
        numberOfStoreys = context.scene.attribute_mass_storeys
        if numberOfStoreys == 0:
            numberOfStoreys = 1
    else:
        numberOfStoreys = storeysSet
    
    # since it is possible to sort typologies in the ui, it can be that the index of the element
    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    item = next(i for i in context.scene.mastro_typology_name_list if i["id"] == typology_id)
    use_list = item.useList
    # uses are listed top to bottom, but they need to
    # be added bottom to top           
    useSplit = use_list.split(";")            
    useSplit.reverse() 
    
    storey_list_A = "1"
    storey_list_B = "1"
    liquidPosition = [] # to count how many liquid uses they are
    fixedStoreys = 0 # to count how many fixed storeys they are
    
    for enum, el in enumerate(useSplit):
        ###setting the values for each use
        for use in projectUses:
            
            if use.id == int(el):
                # number of storeys for the use
                # if a use is "liquid" the number of storeys is set as 00
                if use.liquid: 
                    storeys = "00"
                    liquidPosition.append(enum)
                else:
                    fixedStoreys += use.storeys
                    storeys = str(use.storeys)
                    if use.storeys < 10:
                        storeys = "0" + storeys
                        
                storey_list_A += storeys[0]
                storey_list_B += storeys[1]
                break

    # liquid storeys need to be converted to actual storeys
    storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
    # if the typology has more storeys than the selected mass
    # some extra storeys are added
    if storeyCheck < 1: 
        numberOfStoreys = fixedStoreys + len(liquidPosition)
    storeyLeft = numberOfStoreys - fixedStoreys

    if len(liquidPosition) > 0:
        # the 1 at the start of the number is removed
        storey_list_A = storey_list_A[1:]
        storey_list_B = storey_list_B[1:]
        
        n = storeyLeft/len(liquidPosition)
        liquidStoreyNumber = math.floor(n)

        insert = str(liquidStoreyNumber)
        if liquidStoreyNumber < 10:
            insert = "0" + insert
            
        index = 0
        while index < len(liquidPosition):
            el = liquidPosition[index]
            # if the rounding of the liquid storeys is uneven,
            # the last liquid floor is increased of 1 storey
            if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
                insert = str(liquidStoreyNumber +1) 
                if liquidStoreyNumber +1 < 10:
                    insert = "0" + insert
                
            storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
            storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
            index += 1
        # the 1 is re-added  
        storey_list_A = "1" + storey_list_A
        storey_list_B = "1" + storey_list_B

    data = {"numberOfStoreys" : int(numberOfStoreys),
            "storey_list_A" : int(storey_list_A),
            "storey_list_B" : int(storey_list_B)
            }
    return data

'''Set the depth of the building of the selected edge attribute of the MaStro block'''
class OBJECT_OT_Set_Edge_Attribute_Depth(Operator):
    bl_idname = "object.set_mesh_edge_attribute_depth"
    bl_label = "Set edge depth attributes assigned to the MaStro block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        # mesh.attributes["mastro_number_of_storeys"]
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_edges = [e for e in context.active_object.data.edges if e.select]
        
        for edge in selected_edges:
            edgeIndex = edge.index
            # data = update_mesh_edge_attributes_depth(context, mesh, edgeIndex)
            data = update_mesh_edge_attributes_depth(context)
            mesh.attributes["mastro_block_depth_EDGE"].data[edgeIndex].value = data["blockDepth"]
        # else:
        #     active_vert = bpy.context.scene.previous_selection_vert_id
        #     active_edges =  [e for e in mesh.edges if active_vert in e.vertices]
        #     for edge in active_edges:
        #         edgeIndex = edge.index
        #         data = update_mesh_edge_attributes_depth(context)
        #         mesh.attributes["mastro_block_depth_EDGE"].data[edgeIndex].value = data["blockDepth"]

        bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}
    
'''Block: function to update depth of the building accordingly to the assigned number of storeys'''
# def update_mesh_edge_attributes_depth(context, mesh, edgeIndex, depthSet = None):
def update_mesh_edge_attributes_depth(context, depthSet = None):

    # typology_id = mesh.attributes["mastro_typology_id_EDGE"].data[edgeIndex].value
    # projectUses = context.scene.mastro_use_name_list

    # if the function is run once the user updates the depth of the building,
    # the value is read from context.scene.attribute_block_depth.
    # Else the function is run because the user is updating the depth and
    # in this case the value used is the one stored in each edge of the mesh
    if depthSet == None:
        blockDepth = context.scene.attribute_block_depth
        if blockDepth == 0:
            blockDepth = 18
    else:
        blockDepth = depthSet
    
    data = {"blockDepth" : float(blockDepth)
            }
    return data


# Set the uses and their heights in the selected face attribute of the MaStro mass
class OBJECT_OT_Set_Face_Attribute_Uses(Operator):
    bl_idname = "object.set_mesh_face_attribute_uses"
    bl_label = "Set face attributes assigned to the MaStro mass"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_faces = [p for p in context.active_object.data.polygons if p.select]
        for face in selected_faces:
            faceIndex = face.index
            # data = read_mesh_attributes_uses(context, mesh, faceIndex)
            data = read_mesh_attributes_uses(context)
            mesh.attributes["mastro_typology_id"].data[faceIndex].value = data["typology_id"]
            mesh.attributes["mastro_list_use_id_A"].data[faceIndex].value = data["use_id_list_A"]
            mesh.attributes["mastro_list_use_id_B"].data[faceIndex].value = data["use_id_list_B"]
            mesh.attributes["mastro_list_height_A"].data[faceIndex].value = data["height_A"]
            mesh.attributes["mastro_list_height_B"].data[faceIndex].value = data["height_B"]
            mesh.attributes["mastro_list_height_C"].data[faceIndex].value = data["height_C"]
            mesh.attributes["mastro_list_height_D"].data[faceIndex].value = data["height_D"]
            mesh.attributes["mastro_list_height_E"].data[faceIndex].value = data["height_E"]
            mesh.attributes["mastro_list_void"].data[faceIndex].value = data["void"]
            # number of storeys needs to be updated as well
            numberOfStoreys = mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value
            data = update_mesh_face_attributes_storeys(context, mesh, faceIndex, storeysSet = numberOfStoreys)
            mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value = data["numberOfStoreys"]
            mesh.attributes["mastro_list_storey_A"].data[faceIndex].value = data["storey_list_A"]
            mesh.attributes["mastro_list_storey_B"].data[faceIndex].value = data["storey_list_B"]
           
        bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}

# Set the uses and their heights in the selected edge attribute of the MaStro block
class OBJECT_OT_Set_Edge_Attribute_Uses(Operator):
    bl_idname = "object.set_mesh_edge_attribute_uses"
    bl_label = "Set edge attributes assigned to the MaStro block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_edges = [e for e in context.active_object.data.edges if e.select]
        for edge in selected_edges:
            edgeIndex = edge.index
            # data = read_mesh_attributes_uses(context, mesh, edgeIndex)
            data = read_mesh_attributes_uses(context)
            mesh.attributes["mastro_typology_id_EDGE"].data[edgeIndex].value = data["typology_id"]
            mesh.attributes["mastro_list_use_id_A_EDGE"].data[edgeIndex].value = data["use_id_list_A"]
            mesh.attributes["mastro_list_use_id_B_EDGE"].data[edgeIndex].value = data["use_id_list_B"]
            mesh.attributes["mastro_list_height_A_EDGE"].data[edgeIndex].value = data["height_A"]
            mesh.attributes["mastro_list_height_B_EDGE"].data[edgeIndex].value = data["height_B"]
            mesh.attributes["mastro_list_height_C_EDGE"].data[edgeIndex].value = data["height_C"]
            mesh.attributes["mastro_list_height_D_EDGE"].data[edgeIndex].value = data["height_D"]
            mesh.attributes["mastro_list_height_E_EDGE"].data[edgeIndex].value = data["height_E"]
            mesh.attributes["mastro_list_void_EDGE"].data[edgeIndex].value = data["void"]
            # number of storeys needs to be updated as well
            numberOfStoreys = mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value
            data = update_mesh_edge_attributes_storeys(context, mesh, edgeIndex, storeysSet = numberOfStoreys)
            mesh.attributes["mastro_number_of_storeys_EDGE"].data[edgeIndex].value = data["numberOfStoreys"]
            mesh.attributes["mastro_list_storey_A_EDGE"].data[edgeIndex].value = data["storey_list_A"]
            mesh.attributes["mastro_list_storey_B_EDGE"].data[edgeIndex].value = data["storey_list_B"]
           
        bpy.ops.object.mode_set(mode=mode)
       
        return {'FINISHED'}
    
class OBJECT_OT_Set_Block_Edge_Attribute_Normal(Operator):
    """Set the value which will set to reverse or not reverse the block edge in the block GN"""
    bl_idname = "object.set_mesh_block_edge_attribute_normal"
    bl_label = "Set to normal of the block edge in the block GN"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_edges = [e for e in context.active_object.data.edges if e.select]
        normal = bpy.context.scene.attribute_block_normal
        for edge in selected_edges:
            edgeIndex = edge.index
            mesh.attributes["mastro_inverted_normal_EDGE"].data[edgeIndex].value = normal
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}
    
class OBJECT_OT_Set_Block_Edge_Angle(Operator):
    bl_idname = "object.set_block_edge_attribute_angle"
    bl_label = "Set the corner angle"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_verts = [v for v in context.active_object.data.vertices if v.select]
        angle = bpy.context.scene.attribute_block_side_angle
        for vert in selected_verts:
            vertIndex = vert.index
            mesh.attributes["mastro_side_angle"].data[vertIndex].value = angle
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}
    
    
# function to update the uses and their relative heights accordingly to the assigned typologySet:
# if the function is run by the user when in edit mode the typologyId is read from 
# context.scene.attribute_mass_typology_id, else the typology is updated from the
# typology panel and the typologyId used is the one stored in the face
# def read_mesh_attributes_uses(context, mesh, faceIndex, typologySet=None):
def read_mesh_attributes_uses(context, typologySet=None):
    if typologySet == None:
        typology_id = context.scene.attribute_mass_typology_id
    else:
      typology_id = typologySet
    projectUses = context.scene.mastro_use_name_list
    # since it is possible to sort typologies in the ui, it can be that the index of the element
    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    item = next(i for i in context.scene.mastro_typology_name_list if i["id"] == typology_id)
    use_list = item.useList
    # uses are listed top to bottom, but they need to
    # be added bottom to top           
    useSplit = use_list.split(";")            
    useSplit.reverse() 
    
    use_id_list_A = "1"
    use_id_list_B = "1"
    height_A = "1"
    height_B = "1"
    height_C = "1"
    height_D = "1"
    height_E = "1"
    void = "1"
    
    for enum, el in enumerate(useSplit):
        ### list_use_id
        if int(el) < 10:
            tmpUse = "0" + el
        else:
            tmpUse = el
        use_id_list_A += tmpUse[0]
        use_id_list_B += tmpUse[1]
                                        
        ###setting the values for each use
        for use in projectUses:
            if use.id == int(el):
                void += str(int(use.void))
                #### floor to floor height for each use, stored in A, B, C, ...
                #### due to the fact that arrays can't be used
                #### and array like (3.555, 12.664, 0.123)
                #### is saved as
                #### A (1010) tens
                #### B (1320) units
                #### C (1561) first decimal
                #### D (1562) second decimal
                #### E (1543) third decimal
                #### each array starting with 1 since a number can't start with 0
                height = str(round(use.floorToFloor,3))
                if use.floorToFloor < 10:
                    height = "0" + height
                height_A += height[0]
                height_B += height[1]
                try:
                    height_C += height[3]
                    try:
                        height_D += height[4]
                        try:
                            height_E += height[5]
                        except:
                            height_E += "0"
                    except:
                        height_D += "0"
                        height_E += "0"
                except:
                    height_C += "0"
                    height_D += "0"
                    height_E += "0"
                break

    data = {"typology_id" : typology_id,
            "use_id_list_A" : int(use_id_list_A),
            "use_id_list_B" : int(use_id_list_B),
            "height_A" : int(height_A),
            "height_B" : int(height_B),
            "height_C" : int(height_C),
            "height_D" : int(height_D),
            "height_E" : int(height_E),
            "void" : int(void)
            }
    return data
    
    

class obj_typology_uses_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Obj typology use name id",
           default = 0)
    
    nameId: IntProperty(
           name="nameId",
           description="The id of the name in the main uses list",
           default = 0)
    
    name: StringProperty(
           name="Obj floor use name",
           description="The use associated to that set of floors",
           default="")
    
    storeys: IntProperty(
           name="Number of storeys",
           description="The number of storeys associated to that use",
           default = 0)
    
def update_attributes_mastro_mesh_storeys(self, context):
    if "MaStro mass" in context.object.data: 
        bpy.ops.object.set_mesh_face_attribute_storeys()
    elif "MaStro block" in context.object.data:
        bpy.ops.object.set_mesh_edge_attribute_storeys()
        
def update_attributes_mastro_block_depth(self, context):
    bpy.ops.object.set_mesh_edge_attribute_depth()
    
def update_attributes_block_side_angle(self, context):
    bpy.ops.object.set_block_edge_attribute_angle()
    
# update the block normal
def update_block_normal(self, context):
    bpy.ops.object.set_mesh_block_edge_attribute_normal()

  
# update the block id attribute assigned to the selected object
# this is quite old, maybe better to review
def update_block_name_id(self, context):
    scene = context.scene
    name = scene.mastro_block_names
    # scene.mastro_block_name_current[0].name = " " + name
    scene.mastro_block_name_current[0].name = name
    for n in scene.mastro_block_name_list:
        if n.name == name:
            scene.attribute_mass_block_id = n.id
            scene.mastro_block_name_current[0].id = n.id
            
            obj = context.active_object
            obj.mastro_props['mastro_block_attribute'] = n.id
            break 
        
# this is quite old, maybe better to review
def update_building_name_id(self, context):
    scene = context.scene
    name = scene.mastro_building_names
    scene.mastro_building_name_current[0].name = name
    for n in scene.mastro_building_name_list:
        if n.name == name:
            scene.attribute_mass_building_id = n.id
            scene.mastro_building_name_current[0].id = n.id
            
            obj = context.active_object
            obj.mastro_props['mastro_building_attribute'] = n.id
            break   
    
#Update the typology label in the UI and all the relative data in the selected faces
def update_attributes_mastro_mesh_typology(self, context):
    # update the label
    scene = context.scene
    name = scene.mastro_typology_names
    if "MaStro mass" in context.object.data:
        for n in scene.mastro_typology_name_list:
            if n.name == name:
                scene.attribute_mass_typology_id = n.id
                # update the data accordingly to the typology id
                bpy.ops.object.set_mesh_face_attribute_uses()
                scene.mastro_typology_name_current[0].id = n.id
                scene.mastro_typology_name_current[0].name = name
                break  
    elif "MaStro block" in context.object.data:
        for n in scene.mastro_typology_name_list:
            if n.name == name:
                scene.attribute_mass_typology_id = n.id
                # update the data accordingly to the typology id
                bpy.ops.object.set_mesh_edge_attribute_uses()
                scene.mastro_typology_name_current[0].id = n.id
                scene.mastro_typology_name_current[0].name = name
                break  
            

    
        
    

       