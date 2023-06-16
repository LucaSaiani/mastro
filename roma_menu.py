import bpy
from bpy.types import Menu, Operator
from math import ceil as mathCeil

import csv, os

attribute_set = [
            {"attr" : "roma_vertex_custom_attribute",
             "attr_type" :  "INT",
             "attr_domain" :  "POINT"},
            {"attr" :  "roma_facade_type",
             "attr_type" :  "INT",
             "attr_domain" :  "EDGE"},
            {"attr" :  "roma_number_of_storeys_per_face",
             "attr_type" :  "INT",
             "attr_domain" :  "EDGE"},
            {"attr" :  "roma_plot_name",
             "attr_type" :  "INT",
             "attr_domain" :  "FACE"},
            {"attr" :  "roma_block_name",
             "attr_type" :  "INT",
             "attr_domain" :  "FACE"},
            {"attr" :  "roma_use_name",
             "attr_type" :  "INT",
             "attr_domain" :  "FACE"},
            {"attr" :  "roma_number_of_storeys",
             "attr_type" :  "INT",
             "attr_domain" :  "FACE"},
            {"attr" :  "roma_GEA",
             "attr_type" :  "FLOAT",
             "attr_domain" :  "FACE"}
]

class roma_MenuOperator_convert_to_RoMa_mesh(Operator):
    bl_idname = "object.roma_convert_to_roma"
    bl_label = "Convert the selected mesh to a RoMa mesh"
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        selected_meshes = [obj for obj in selected_objects if obj.type == 'MESH']
        mode = None
        for obj in selected_meshes:
            mesh = obj.data
            mesh["RoMa object"] = True
            for a in attribute_set:
                try:
                    mesh.attributes[a["attr"]]
                except:
                    mesh.attributes.new(name=a["attr"], type=a["attr_type"], domain=a["attr_domain"])
     
        return {'FINISHED'}
    
class RoMa_MenuOperator_PrintData(Operator):
    bl_idname = "object.roma_print_data"
    bl_label = "Print the data of the mass"

    def execute(self, context):
        # roma_list = []
        csvData = []
        header = ["Plot Name", "Block Name", "Use", "Number of Storeys", "GEA"]
        csvData.append(header)
        objects = [obj for obj in bpy.context.scene.objects]
        for obj in objects:
            if obj.type == "MESH":
                obj.update_from_editmode()
                mesh = obj.data
                data = get_mass_data(mesh)
        
        for row in data:
            print(row)       
        
        return {'FINISHED'}
    
class RoMa_MenuOperator_ExportCSV(Operator):
    bl_idname = "object.roma_export_csv"
    bl_label = "Export data as CSV"

    def execute(self, context):
        # roma_list = []
        plotName = None
        blockName = None
        use = None
        storeys = None
        csvData = []
        header = ["Plot Name", "Block Name", "Use", "Number of Storeys", "GEA"]
        csvData.append(header)
        objects = [obj for obj in bpy.context.scene.objects]
        for obj in objects:
            if obj.type == "MESH":
                mesh = obj.data
                csvData = get_mass_data(mesh)
        
        current_file_path = bpy.context.blend_data.filepath

        # Get the current working folder
        current_folder = os.path.dirname(bpy.path.abspath(current_file_path))
        
        filename = "blenderData"

        savingPath = current_folder + "/" + filename + ".csv"
        with open(savingPath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csvData)

        print(f"Data saved to {savingPath}")
        return {'FINISHED'}

class RoMa_Menu(Menu):
    bl_idname = "VIEW3D_MT_custom_menu"
    bl_label = "RoMa"

    def draw(self, context):
        layout = self.layout
        layout.operator(roma_MenuOperator_convert_to_RoMa_mesh.bl_idname)
        layout.operator(RoMa_MenuOperator_PrintData.bl_idname)
        layout.operator(RoMa_MenuOperator_ExportCSV.bl_idname)
   
# Callback function to add drop down menu
def roma_menu(self, context):
    layout = self.layout
    layout.menu(RoMa_Menu.bl_idname)

def get_mass_data(mesh):
    data = []
    if "roma_plot_name" in mesh.attributes:
        plotNameAttributes = mesh.attributes["roma_plot_name"].data
        blockNameAttributes = mesh.attributes["roma_block_name"].data
        useAttributes = mesh.attributes["roma_use_name"].data
        storeysAttributes = mesh.attributes["roma_number_of_storeys"].data
                    
        for index, attr in enumerate(plotNameAttributes):
            #print(plotNameAttributes[index].value, blockNameAttributes[index].value,useAttributes[index].value,storeysAttributes[index].value  )
            plotId = plotNameAttributes[index].value
            if plotId == 0:
                plotName = None
            else:
                for n in bpy.context.scene.roma_plot_name_list:
                    if n.index == plotId:
                        plotName = n.name
                        break
            blockName = blockNameAttributes[index].value
            use = useAttributes[index].value
            storeys = storeysAttributes[index].value
            # if floor_GEA >= 0:
            #print([plotName, blockName, use, storeys])
            data.append([plotName, blockName, use, storeys])
        # print()
        # print()
            
    return(data)


# import bpy
# import gpu
# from gpu_extras.batch import batch_for_shader

# vertices = (
#     (10, 10), (300, 10),
#     (10, 200), (300, 200))

# indices = (
#     (0, 1, 2), (2, 1, 3))

# shader = gpu.shader.from_builtin('UNIFORM_COLOR')
# batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)


# def draw():
#     shader.bind()
#     shader.uniform_float("color", (0, 0.5, 0.5, 1.0))
#     batch.draw(shader)

# class ModalDrawOperator(bpy.types.Operator):
#     bl_idname = "view3d.modal_operator"
#     bl_label = "Test Operator"

#     def invoke(self, context, event):
#         print("miao")
#         context.area.type = 'VIEW_3D'
#         if context.area.type != 'VIEW_3D':
#             print("Viewport not found")
#             return {'CANCELLED'}

#         bpy.types.SpaceView3D.draw_handler_add(draw, (), 'UI', 'POST_PIXEL')
#         print("done")
#         return {'FINISHED'}

# def register():
#     bpy.utils.register_class(ModalDrawOperator)

# def unregister():
#     bpy.utils.unregister_class(ModalDrawOperator)

# if __name__ == "__main__":
#     register()
#     bpy.ops.view3d.modal_operator('INVOKE_DEFAULT')

#######################################
#https://blender.stackexchange.com/questions/41216/how-can-i-add-a-text-help-window-and-a-help-button-into-the-3d-view


# bl_info = {
#     "name": "Floating demo",
#     "author": "sambler",
#     "version": (1,0),
#     "blender": (2, 75, 0),
#     "location": "view3D",
#     "description": "Demo floating panel in the 3dview",
#     "category": "User Interface",
# }

# import bpy
# import bgl
# import blf

# import gpu
# from gpu_extras.batch import batch_for_shader

# shader = gpu.shader.from_builtin('FLAT_COLOR')

# def draw_poly(points):
#     for i in range(len(points)):
#             bgl.glVertex2f(points[i][0],points[i][1])

# def draw_callback_px(self, context):
#     panel_points = [(10.0, 10.0),
#                     (10.0, 100.0),
#                     (150.0, 100.0),
#                     (150.0, 10.0)]

#     # draw poly for floating panel
#     bgl.glClearColor(0.3, 0.3, 0.3, 1.0)
#     bgl.glEnable(bgl.GL_BLEND)

#     color = (1.0, 1.0, 1.0, 1.0)
#     panel_color = [color] * len(panel_points)

#     batch = batch_for_shader(shader, 'LINES', {"pos": panel_points, "color": panel_color})
#     shader.bind()
#     batch.draw(shader)

#     # draw outline
#     color = (0.1, 0.1, 0.1, 1.0)
#     outline_points = panel_points + [panel_points[0]]  # Add the first point to close the loop
#     outline_color = [color] * len(outline_points)
#     outline_batch = batch_for_shader(shader, 'LINES', {"pos": outline_points, "color": outline_color})
#     outline_batch.draw(shader)

#     font_id = 0
#     # draw some text
#     color = (0.8, 0.8, 0.8, 1.0)
#     blf.position(font_id, 15, 80, 0)
#     blf.size(font_id, 14)
#     blf.draw(font_id, "Hello World")

#     blf.position(font_id, 15, 50, 0)
#     blf.draw(font_id, "I am floating")

#     # restore opengl defaults
#     color = (0.0, 0.0, 0.0, 1.0)
#     bgl.glDisable(bgl.GL_BLEND)

# class ModalFloatyOperator(bpy.types.Operator):
#     """Draw a floating panel"""
#     bl_idname = "view3d.modal_floaty_operator"
#     bl_label = "Demo floating panel Operator"

#     def modal(self, context, event):
#         context.area.tag_redraw()

#         if event.type == 'MOUSEMOVE':
#             self.mouse_path.append((event.mouse_region_x, event.mouse_region_y))

#         elif event.type == 'LEFTMOUSE':
#             bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
#             return {'FINISHED'}

#         elif event.type in {'RIGHTMOUSE', 'ESC'}:
#             bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
#             return {'CANCELLED'}

#         return {'RUNNING_MODAL'}

#     def invoke(self, context, event):
#         if context.area.type == 'VIEW_3D':
#             # the arguments we pass the the callback
#             args = (self, context)
#             # Add the region OpenGL drawing callback
#             # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
#             self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

#             self.mouse_path = []

#             context.window_manager.modal_handler_add(self)
#             return {'RUNNING_MODAL'}
#         else:
#             self.report({'WARNING'}, "View3D not found, cannot run operator")
#             return {'CANCELLED'}

# def menu_funk(self, context):
#     self.layout.operator(ModalFloatyOperator.bl_idname, text="Modal Float Operator")


# def register():
#     bpy.utils.register_class(ModalFloatyOperator)
#     bpy.types.VIEW3D_MT_view.append(menu_funk)


# def unregister():
#     bpy.utils.unregister_class(ModalFloatyOperator)
#     bpy.types.VIEW3D_MT_view.remove(menu_funk)

# if __name__ == "__main__":
#     register()