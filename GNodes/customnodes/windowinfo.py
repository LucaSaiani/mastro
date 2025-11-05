import bpy 
from bpy_extras.view3d_utils import location_3d_to_region_2d

from ..utils.node_utils import create_new_nodegroup, set_socket_defvalue

class MASTRO_NG_windowinfo(bpy.types.GeometryNodeCustomGroup):
    bl_idname = "MastroGNWindowInfo"
    bl_label = "Window info"

    # use_scene_cam: bpy.props.BoolProperty(
    #     default=True,
    #     name="Use Active Camera",
    #     description="Automatically update the pointer to the active scene camera",
    #     )

    def view_obj_poll(self, obj):
        return obj.type == 'MESH'

    view_obj: bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=view_obj_poll,
        )

    @classmethod
    def poll(cls, context):
        return True

    def init(self, context):
        name = f".{self.bl_idname}"
        ng = bpy.data.node_groups.get(name)
        if (ng is None):
            ng = create_new_nodegroup(name,
                out_sockets={
                    "View" : "NodeSocketVector",
                    # "Camera Object" : "NodeSocketObject",
                    # "Field of View" : "NodeSocketFloat",
                    # "Shift X" : "NodeSocketFloat",
                    # "Shift Y" : "NodeSocketFloat",
                    # "Clip Start" : "NodeSocketFloat",
                    # "Clip End" : "NodeSocketFloat",
                    # "Resolution X" : "NodeSocketInt",
                    # "Resolution Y" : "NodeSocketInt",
                },
            )
         
        ng = ng.copy() #always using a copy of the original ng
        
        self.node_tree = ng
        self.label = self.bl_label

        return None

    def copy(self, node):
        self.node_tree = node.node_tree.copy()
        return None

    def update(self):
        scene = bpy.context.scene
        view_obj = self.view_obj
        # set_socket_defvalue(self.node_tree, 0, value=view_obj)
        
        if (view_obj and view_obj.data):
            matrix = view_obj.matrix_world
            area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            space = area.spaces.active
            location = matrix @ view_obj.location # convert the coordinates from local to world
            # coords_2d = location_3d_to_region_2d(region, space.region_3d, location)
            # coords_2d = space.region_3d.view_matrix
            matrix_world = space.region_3d.view_matrix.inverted()
            location = matrix_world.to_translation()
            rotation = matrix_world.to_euler()
            
            print(location, rotation)
            # coords = view_obj.matrix_data @ view_obj.location
            set_socket_defvalue(self.node_tree, 0, value=rotation)
            # set_socket_defvalue(self.node_tree, 2, value=cam_obj.data.shift_x)
            # set_socket_defvalue(self.node_tree, 3, value=cam_obj.data.shift_y)
            # set_socket_defvalue(self.node_tree, 4, value=cam_obj.data.clip_start)
            # set_socket_defvalue(self.node_tree, 5, value=cam_obj.data.clip_end)
            # set_socket_defvalue(self.node_tree, 6, value=scene.render.resolution_x)
            # set_socket_defvalue(self.node_tree, 7, value=scene.render.resolution_y)
        return None

    def draw_label(self,):
        return self.bl_label

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "view_obj", text="", icon="MESH_CUBE")
        # sub = row.row(align=True)
        # sub.active = not self.use_scene_cam

        # if (self.use_scene_cam):
        #       sub.prop(bpy.context.scene, "camera", text="", icon="CAMERA_DATA")
        # else: sub.prop(self, "camera_obj", text="", icon="CAMERA_DATA")

        # row.prop(self, "use_scene_cam", text="", icon="SCENE_DATA")

        return None
        
    @classmethod
    def update_all(cls):
        """search for all nodes of this type and update them"""
        
        for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
            n.update()
            
        return None 