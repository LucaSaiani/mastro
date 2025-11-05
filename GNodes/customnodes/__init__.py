import bpy

from .windowinfo import MASTRO_NG_windowinfo

classes = (
    MASTRO_NG_windowinfo,
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