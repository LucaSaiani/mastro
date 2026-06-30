import bpy
import blf
import bmesh
import gpu

from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from bpy.types import Operator
from mathutils import Vector

from ...Utils.mastro_preferences.get_preferences  import get_prefs
from .mastro_arch.overlay_block import show_block_overlay
from .mastro_arch.overlay_wall import show_wall_overlay
from .mastro_street.overlay_street import show_street_overlay
from .mastro_street.overlay_street_sectors import show_street_sector_overlay


class VIEW_3D_OT_show_mastro_attributes(Operator):
    """Toggle the viewport attribute overlays (typology, storeys, normals, etc.)."""
    bl_idname = "wm.show_mastro_attributes"
    bl_label = "Show MaStro attributes"

    _handle_2D = None  # 2D text overlay drawn in pixel-space (POST_PIXEL)
    _handle_3D = None  # 3D geometry overlay drawn in world-space (POST_VIEW)
    
    @staticmethod
    def handle_add_2D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_2D is None:
            VIEW_3D_OT_show_mastro_attributes._handle_2D = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_show_attributes_2D, (self, context),
                                                                        'WINDOW',
                                                                        'POST_PIXEL')
    @staticmethod
    def handle_add_3D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_3D is None:
            VIEW_3D_OT_show_mastro_attributes._handle_3D = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_show_attributes_3D, (self, context),
                                                                        'WINDOW',
                                                                        'POST_VIEW')

    @staticmethod
    def handle_remove_2D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_2D is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_mastro_attributes._handle_2D, 'WINDOW')
        VIEW_3D_OT_show_mastro_attributes._handle_2D = None
    
    @staticmethod
    def handle_remove_3D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_3D is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_mastro_attributes._handle_3D, 'WINDOW')
        VIEW_3D_OT_show_mastro_attributes._handle_3D = None

    
    def execute(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_2D is None:
            self.handle_add_2D(self, context)
            context.area.tag_redraw()
        else:
            self.handle_remove_2D(self, context)
            context.area.tag_redraw()
            
        if VIEW_3D_OT_show_mastro_attributes._handle_3D is None:
            self.handle_add_3D(self, context)
            context.area.tag_redraw()
        else:
            self.handle_remove_3D(self, context)
            context.area.tag_redraw()
        return {'FINISHED'}
    
def draw_selection_overlay(context):
    """Draw a colored edge/face overlay on the active MaStro object in edit mode."""
    obj = bpy.context.active_object
    if hasattr(obj, "data") and obj.data is not None and "MaStro object" in obj.data:
        prefs = get_prefs()
        mesh = obj.data
        if mesh.is_editmode:
            if "MaStro mass" in obj.data:
                coords = []
                edgeIndices = []
                shader = gpu.shader.from_builtin('UNIFORM_COLOR')
                
                if mesh.is_editmode:
                    bm = bmesh.from_edit_mesh(mesh)
                    
                    # draw the edges of the selected object
                    for vert in bm.verts:
                        # print(vert.index, vert.co, obj.matrix_world @ vert.co)
                        coords.append(obj.matrix_world @ vert.co)
                        
                    for edge in bm.edges:
                        tmpEdge = (edge.verts[0].index, edge.verts[1].index)
                        edgeIndices.append(tmpEdge)
                        
                    
                    batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=edgeIndices)
                    
                    r, g, b, a = [c for c in prefs.massEdgeColor]
                    shader.uniform_float("color", (r, g, b, a))
                
                    gpu.state.line_width_set(prefs.massEdgeSize)
                    gpu.state.blend_set("ALPHA")
                    batch.draw(shader)
                    
                    # draw the selected faces
                    if bpy.context.scene.tool_settings.mesh_select_mode[2]:
                        faces = [f for f in bm.faces if f.select == True]
                        
                        # create a new Bmesh with only the newly created faces
                        dbm = bmesh.new()
                        for face in faces:
                            dbm.faces.new((dbm.verts.new(obj.matrix_world @ v.co, v) for v in face.verts), face)
                        dbm.verts.index_update()    

                        dVertices = [v.co for v in dbm.verts]
                        dFaceindices = [(loop.vert.index for loop in looptris) for looptris in dbm.calc_loop_triangles()]
                        # dEdgeindices = [(v.index for v in e.verts) for e in dbm.edges]
                        batch = batch_for_shader(shader, 'TRIS', {"pos": dVertices}, indices=dFaceindices)
                        r, g, b, a = [c for c in prefs.massFaceColor]
                        shader.uniform_float("color", (r, g, b, a))       
                        # gpu.state.blend_set("NONE")
                        batch.draw(shader)
                        
                        dbm.free()
                        bm.free()
            
                    if bpy.context.scene.tool_settings.mesh_select_mode[1]:
                        show_wall_overlay(obj)

            elif "MaStro block" in obj.data:
                show_block_overlay(obj)
            elif "MaStro street" in obj.data:
                show_street_overlay(obj)
                show_street_sector_overlay(obj)

def draw_main_show_attributes_2D(context):
    """Draw text labels (typology, storeys, normals) at each edge/face centre in pixel-space."""
    obj = bpy.context.active_object
    if obj is None:
        return
    if not hasattr(obj, "data"):
        return
    if "MaStro object" not in obj.data:
        return
    has_mass = "MaStro mass" in obj.data
    has_block = "MaStro block" in obj.data
    if not has_mass and not has_block:
        return
    
    #if hasattr(obj, "data") and "MaStro object" in obj.data and ("MaStro mass" in obj.data or "MaStro block" in obj.data):
    # obj.update_from_editmode()
    prefs = get_prefs()
    scene = context.scene
        
    mesh = obj.data
    matrix = obj.matrix_world
    
    if mesh.is_editmode:
        bm = bmesh.from_edit_mesh(mesh)
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()    
    bm.faces.ensure_lookup_table()      
    
    if "MaStro mass" in obj.data:
        # bm_wall = bm.edges.layers.int["mastro_wall_id"]
        bm_normal = bm.edges.layers.bool["mastro_inverted_normal"]
    
        # bm_block = bm.faces.layers.int["mastro_block_id"]
        # bm_building = bm.faces.layers.int["mastro_building_id"]
        bm_typology = bm.faces.layers.int["mastro_typology_id"]
        bm_storey = bm.faces.layers.int["mastro_number_of_storeys"]
        bm_floor = bm.faces.layers.int["mastro_floor_id"]
    elif "MaStro block" in obj.data:
        bm_normal = bm.edges.layers.bool["mastro_inverted_normal_EDGE"]
        bm_typology = bm.edges.layers.int["mastro_typology_id_EDGE"]
        bm_storey = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]
        

    region = bpy.context.region
    
    
    # Detect if Quadview to get drawing area
    if not context.space_data.region_quadviews:
        rv3d = bpy.context.space_data.region_3d
    else:
        # verify area
        if context.area.type != 'VIEW_3D' or context.space_data.type != 'VIEW_3D':
            return
        i = -1
        for region in context.area.regions:
            if region.type == 'WINDOW':
                i += 1
                if context.region.id == region.id:
                    break
        else:
            return
        rv3d = context.space_data.region_quadviews[i]

    #gpu.state.blend_set('ALPHA')
    
    # center = obj.location
    # print(obj.location, "posizione",pos.x, pos.y, pos.z)
    # coord = view3d_utils.location_3d_to_region_2d(region, rv3d, center)
    
    font_info = {
        "font_id": 0,
        "handler": None,
    }
    
    font_info["font_id"] = 0
    
    font_id = font_info["font_id"]
    # blf.position(font_id, coord.x, coord.y, 0)
    r, g, b, a = [c for c in prefs.fontColor]
    blf.color(font_id, r, g, b, a)
    font_size =  prefs.fontSize
    blf.size(font_id, font_size)
    
    # multi line text
    # https://blender.stackexchange.com/questions/31780/multi-line-text-in-blf-with-multi-colour-option
    line_height = (blf.dimensions(font_id, "M")[1] * 1.45)
    half_line_height = line_height /2
    
    cr = "Carriage Return"
                
    for bmEdge in bm.edges:
        vertices = bmEdge.verts
        A = bm.verts[vertices[0].index].co
        B = bm.verts[vertices[1].index].co
        edge_center = Vector()
        edge_center.x = (A.x + B.x)/2
        edge_center.y = (A.y + B.y)/2
        edge_center.z = (A.z + B.z)/2
        center = matrix @ edge_center # convert the coordinates from local to world
        
        line_width = 0
        vert_offset = 0
        
        # idWall = bmEdge[bm_wall]
        normal = bmEdge[bm_normal]
        
        text_edge = []
        text_typology = ""
        text_normal = ""
        text_storey = ""
        
        if "MaStro block" in obj.data:
            idUse = bmEdge[bm_typology]
            storey = bmEdge[bm_storey]
            if bpy.context.window_manager.mastro_toggle_typology_name:   
                for n in scene.mastro_typology_name_list:
                    if n.id == idUse:
                        if n.name != "":
                            text_typology = (("Typology: " + n.name), 0)
                            if blf.dimensions(font_id, text_typology[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_typology[0])[0]
                            vert_offset += half_line_height
                            text_edge.append(text_typology)
                            text_edge.append(cr)           
                            break
            if bpy.context.window_manager.mastro_toggle_storey_number:  
                text_storey = (("N° of storeys: " + str(storey)), 0)
                if blf.dimensions(font_id, text_storey[0])[0] > line_width:
                            line_width = blf.dimensions(font_id, text_storey[0])[0]
                vert_offset += half_line_height
                text_edge.append(text_storey)
                text_edge.append(cr)  
            if bpy.context.window_manager.mastro_toggle_block_normal: 
                if normal == True:   
                    symbol = "⥌"
                    text_normal = (symbol, 0)
                    line_width = blf.dimensions(font_id, symbol)[0] 
                    vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)/2
                    text_edge.append(text_normal)
                        
                        
        # if bpy.context.window_manager.toggle_wall_name:   
        #     for n in bpy.context.scene.mastro_wall_name_list:
        #         if n.id == idWall:
        #             text_edge = (n.name, 0)
        #             line_width = blf.dimensions(font_id, n.name)[0]
        #             vert_offset = -1 * half_line_height
        #             text_edge.append(text_edge)
        #             text_edge.append(cr)
        #             break
        if "MaStro mass" in obj.data:
            if bpy.context.window_manager.mastro_toggle_wall_normal:
                if normal == True:   
                    symbol = "⥌"
                    text_normal = (symbol, 0)
                    line_width = blf.dimensions(font_id, symbol)[0]
                    vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)/2
                    text_edge.append(text_normal)
                
        coord = view3d_utils.location_3d_to_region_2d(region, rv3d, center)
        # coord = center
        x_offset = (-1 * line_width) / 2
        y_offset = -1 * vert_offset
        
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                for pstr in text_edge:
                    if len(pstr) == 2:
                        string = pstr[0]
                        text_width, text_height = blf.dimensions(font_id, string)
                        blf.position(font_id, (coord.x + x_offset), (coord.y + y_offset), 0)
                        blf.draw(font_id, string)
                        x_offset += text_width
                    else:
                        x_offset = (-1 * line_width) / 2
                        y_offset -= line_height
                break
    
    if "MaStro mass" in obj.data:
        for bmFace in bm.faces:
            center_local = bmFace.calc_center_median()
            
            center = matrix @ center_local # convert the coordinates from local to world
            # idBlock = bmFace[bm_block]
            # idBuilding = bmFace[bm_building]
            idUse = bmFace[bm_typology]
            idFloor = bmFace[bm_floor]
            storey = bmFace[bm_storey]
            
            line_width = 0
            vert_offset = 0
            
            text_face = []
            text_block = ""
            text_building = ""
            text_typology = ""
            text_storey = ""
            text_floor = ""
            
            # blockId
            if bpy.context.window_manager.mastro_toggle_block_name:   
                blockId = obj.mastro_props['mastro_block_attribute']
                for n in scene.mastro_block_name_list:
                    if n.id == blockId:
                        if n.name != "":
                            text_block = (("Block: " + n.name), 0)
                            line_width = blf.dimensions(font_id, text_block[0])[0]
                            vert_offset = half_line_height
                            text_face.append(text_block)
                            text_face.append(cr)
                        break
                
            # buildingId
            if bpy.context.window_manager.mastro_toggle_building_name:   
                buildingId = obj.mastro_props['mastro_building_attribute']
                for n in scene.mastro_building_name_list:
                    if n.id == buildingId:
                        if n.name != "":
                            text_building = (("Building: " + n.name), 0)
                            if blf.dimensions(font_id, text_building[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_building[0])[0]
                                vert_offset += half_line_height
                            text_face.append(text_building)
                            text_face.append(cr)
                        break
                
            # if bpy.context.window_manager.mastro_toggle_block_name:   
            #     for n in bpy.context.scene.mastro_block_name_list:
            #         if n.id == idBlock:
            #             text_block = (("Block: " + n.name), 0)
            #             line_width = blf.dimensions(font_id, text_block[0])[0]
            #             vert_offset = half_line_height
            #             text.append(text_block)
            #             text.append(cr)
            #             break
            # if bpy.context.window_manager.mastro_toggle_building_name:   
            #     for n in bpy.context.scene.mastro_building_name_list:
            #         if n.id == idBuilding:
            #             text_building = (("Building: " + n.name), 0)
            #             if blf.dimensions(font_id, text_building[0])[0] > line_width:
            #                 line_width = blf.dimensions(font_id, text_building[0])[0]
            #             vert_offset += half_line_height
            #             text.append(text_building)
            #             text.append(cr)
            #             break
            if bpy.context.window_manager.mastro_toggle_typology_name:   
                for n in scene.mastro_typology_name_list:
                    if n.id == idUse:
                        if n.name != "":
                            text_typology = (("Typology: " + n.name), 0)
                            if blf.dimensions(font_id, text_typology[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_typology[0])[0]
                            vert_offset += half_line_height
                            text_face.append(text_typology)
                            text_face.append(cr)           
                            break
            if bpy.context.window_manager.mastro_toggle_floor_name:   
                for n in scene.mastro_floor_name_list:
                    if n.id == idFloor:
                        text_floor = (("Floor: " + n.name), 0)
                        if blf.dimensions(font_id, text_floor[0])[0] > line_width:
                            line_width = blf.dimensions(font_id, text_floor[0])[0]
                        vert_offset += half_line_height
                        text_face.append(text_floor)
                        text_face.append(cr)           
                        break
            if bpy.context.window_manager.mastro_toggle_storey_number:  
                text_storey = (("N° of storeys: " + str(storey)), 0)
                if blf.dimensions(font_id, text_storey[0])[0] > line_width:
                            line_width = blf.dimensions(font_id, text_storey[0])[0]
                vert_offset += half_line_height
                text_face.append(text_storey)
        
        
            coord = view3d_utils.location_3d_to_region_2d(region, rv3d, center)
            x_offset = (-1 * line_width) / 2
            y_offset = vert_offset - half_line_height
            # print(text_face)
            for pstr in text_face:
                if len(pstr) == 2:
                    string = pstr[0]
                    text_width, text_height = blf.dimensions(font_id, string)
                    blf.position(font_id, (coord.x + x_offset), (coord.y + y_offset), 0)
                    blf.draw(font_id, string)
                    x_offset += text_width
                else:
                    x_offset = (-1 * line_width) / 2
                    y_offset -= line_height
    bm.free()

def draw_main_show_attributes_3D(context):
    """Dispatch the correct geometry overlay (block/wall/street) based on object type and mode."""
    obj = bpy.context.active_object

    if obj is None:
        return
    if not hasattr(obj, "data"):
        return
    if "MaStro object" not in obj.data:
        return
    
    # if hasattr(obj, "data") and "MaStro object" in obj.data:
    mesh = obj.data
    if mesh.is_editmode == True and bpy.context.window_manager.mastro_toggle_show_data_edit_mode:
        draw_selection_overlay(obj)
    elif mesh.is_editmode == False:
        if "MaStro street" in obj.data and bpy.context.window_manager.mastro_toggle_street_color:
            show_street_overlay(obj)
        if "MaStro mass" in obj.data and bpy.context.window_manager.mastro_toggle_wall_type:
            show_wall_overlay(obj)
        if "MaStro block" in obj.data and bpy.context.window_manager.mastro_toggle_block_typology_color:
            show_block_overlay(obj)
    
def draw_callback_px_show_attributes_2D(self, context):
    if not context.space_data.overlay.show_overlays:
        return
    draw_main_show_attributes_2D(context)


def draw_callback_px_show_attributes_3D(self, context):
    if not context.space_data.overlay.show_overlays:
        return
    draw_main_show_attributes_3D(context)
        

def update_show_attributes(self, context):
    bpy.ops.wm.show_mastro_attributes()