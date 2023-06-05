import bpy
from bpy.types import Menu, Operator

import csv

class RoMa_MenuOperator(Operator):
    bl_idname = "object.custom_menu_operator"
    bl_label = "Print data"

    def execute(self, context):
        roma_list = []
        csvData = []
        header = ["Plot Name", "Block Name", "Use", "Number of Storeys"]
        csvData.append(header)
        objects = [obj for obj in bpy.context.scene.objects]
        for obj in objects:
            if obj.type == "MESH":
                mesh = obj.data
                if "roma_plot_name" in mesh.attributes:
                    roma_list.append(mesh)
                    
        for el in roma_list:
            plotName = el.attributes["roma_plot_name"].data[0].value
            blockName = el.attributes["roma_block_name"].data[0].value
            use = el.attributes["roma_use_name"].data[0].value
            storeys = el.attributes["roma_number_of_storeys"].data[0].value
            csvData.append([plotName, blockName, use, storeys])
        
        filename = "blenderData.csv"
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csvData)

        print(f"Data saved to {filename}")
        
        
        return {'FINISHED'}

class RoMa_Menu(Menu):
    bl_idname = "VIEW3D_MT_custom_menu"
    bl_label = "RoMa"

    def draw(self, context):
        layout = self.layout
        layout.operator(RoMa_MenuOperator.bl_idname)
        
        
# import bpy

# objs = bpy.context.selected_objects

# for obj in objs:
#     mesh = obj.data
#     if "roma_plot_name" in mesh.attributes:
#         value = mesh.attributes["roma_plot_name"].data[0].value
#         print(value)