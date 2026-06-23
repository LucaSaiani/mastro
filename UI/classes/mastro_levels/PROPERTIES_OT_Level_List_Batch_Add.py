from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty, StringProperty, EnumProperty

from ....Utils.mastro_levels.sort_level_list import sort_level_list
from ....Utils.update_attributes import update_all_mastro_plans_level


class PROPERTIES_OT_Level_List_Batch_Add(Operator):
    """Add several levels at once, evenly spaced by increment"""
    bl_idname = "mastro_level_list.batch_add"
    bl_label = "Add Levels"
    bl_options = {'REGISTER', 'UNDO'}

    start_level: FloatProperty(
        name="Start Level", description="Elevation of the first level", precision=5, subtype="DISTANCE",
    )
    # Kept non-negative (subtype="DISTANCE" clamps negative keyboard input
    # in some Blender UI contexts); direction is a separate enum instead so
    # the increment is still freely usable as a "step up" or "step down".
    increment: FloatProperty(
        name="Increment", description="Elevation step between levels",
        default=3.0, precision=5, subtype="DISTANCE", min=0.0,
    )
    increment_sign: EnumProperty(
        name="Direction",
        description="Whether the increment is added or subtracted at each step",
        items=(('POSITIVE', "Positive", "Add the increment at each step"),
               ('NEGATIVE', "Negative", "Subtract the increment at each step")),
        default='POSITIVE',
    )
    count: IntProperty(
        name="Number of Levels", description="How many levels to create", default=1, min=1,
    )
    name_template: StringProperty(
        name="Name Template",
        description="Use {n} as placeholder for the level number, e.g. 'level_{n}'",
        default="level_{n}",
    )
    start_number: IntProperty(
        name="Start Number", description="First number used in the name template", default=1, min=0,
    )
    digits: IntProperty(
        name="Digits", description="Minimum number of digits used for {n}, zero-padded", default=2, min=1,
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(self, "start_level")
        layout.prop(self, "increment")
        layout.row().prop(self, "increment_sign", expand=True)
        layout.prop(self, "count")
        layout.separator()
        layout.prop(self, "name_template")
        layout.prop(self, "start_number")
        layout.prop(self, "digits")

    def execute(self, context):
        if "{n}" not in self.name_template:
            self.report({'ERROR'}, "Name template must contain {n}")
            return {'CANCELLED'}

        scene = context.scene
        collection = scene.mastro_level_list

        ids = [el.id for el in collection]
        next_id = max(ids) + 1 if ids else 1
        signed_increment = -self.increment if self.increment_sign == 'NEGATIVE' else self.increment

        # Same guard as PROPERTIES_OT_Level_List_New_Item: skip the
        # per-field update/sort while building all items, then sort once.
        scene["mastro_level_list_batch_update"] = True
        for i in range(self.count):
            item = collection.add()
            item.id = next_id
            next_id += 1
            item.level = self.start_level + i * signed_increment
            number = str(self.start_number + i).zfill(self.digits)
            item.name = self.name_template.replace("{n}", number)
        del scene["mastro_level_list_batch_update"]

        sort_level_list(scene)
        update_all_mastro_plans_level(context)

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
