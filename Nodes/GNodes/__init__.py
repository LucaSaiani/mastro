
from .filter_by import mastro_GN_filter_by_OT
from .mastro_GN_separate_by_wall_type import mastro_GN_separate_by_wall_type
from .window_info import mastro_GN_windowinfo

classes = (
    mastro_GN_filter_by_OT,
    mastro_GN_separate_by_wall_type,
    mastro_GN_windowinfo,
    )

# def register():

#     bpy.types.Scene.windowInfoNodeCounter = bpy.props.IntProperty(
#                                         name="Window Into Node Counter",
#                                         default=0,
#                                         description="Keep track of the number of Window Info Nodes that are used in the scene")
#                                         # update = mastro_massing.update_attributes_mastro_mesh)

#     return None

# def unregister():

#     del bpy.types.Scene.windowInfoNodeCounter 

#     return None