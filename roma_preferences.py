import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import IntProperty, FloatVectorProperty #StringProperty, FloatProperty, BoolProperty

class roma_addon_preferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    # bl_idname = __name__
    bl_idname = __package__

    # filepath: StringProperty(
    #     name="Example File Path",
    #     subtype='FILE_PATH',
    # )
    # number: IntProperty(
    #     name="Example Number",
    #     default=4,
    # )
    # boolean: BoolProperty(
    #     name="Example Boolean",
    #     default=False,
    # )
    fontSize: IntProperty(
        name="Font Size",
        min = 8,
        default = 25
    )
    
    fontColor: bpy.props.FloatVectorProperty(
                 name = "Font Color Picker",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1.0, 1.0, 0.0, 1.0))

    def draw(self, context):
        layout = self.layout
        # layout.label(text="RoMa addon preferences")
        # layout.prop(self, "filepath")
        # layout.prop(self, "number")
        # layout.prop(self, "boolean")
        row = layout.row()
        row.prop(self, "fontSize", text = "Font Size")
        row.prop(self, "fontColor", text = "Font Color")
        
class OBJECT_OT_roma_addon_prefs(Operator):
    """Display example preferences"""
    bl_idname = "object.roma_addon_prefs"
    bl_label = "RoMa add-on Preferences"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        preferences = context.preferences
        # addon_prefs = preferences.addons[__name__].preferences
        addon_prefs = preferences.addons[__package__].preferences


        # info = ("Path: %s, Number: %d, Boolean %r" %
        #         (addon_prefs.filepath, addon_prefs.number, addon_prefs.boolean))
        info = ("Font Size: %s, Font color: %d" %
                (addon_prefs.fontSize, addon_prefs.fontColor))

        self.report({'INFO'}, info)
        # print(info)

        return {'FINISHED'}