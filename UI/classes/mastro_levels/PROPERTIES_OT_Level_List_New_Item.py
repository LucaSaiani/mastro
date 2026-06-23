from bpy.types import Operator

from ....Utils.mastro_levels.sort_level_list import sort_level_list
from ....Utils.update_attributes import update_all_mastro_plans_level


class PROPERTIES_OT_Level_List_New_Item(Operator):
    """Add a new level to the project"""
    bl_idname = "mastro_level_list.new_item"
    bl_label = "Add level"
    bl_description = "Add a new level to the scene"

    def execute(self, context):
        scene = context.scene
        collection = scene.mastro_level_list

        # Assigning item.name/item.level below would normally trigger their
        # update callback and re-sort the list after every single field is
        # set (while the item is still half-initialised). Suppress that and
        # sort once, after the new item is fully populated.
        scene["mastro_level_list_batch_update"] = True
        item = collection.add()
        ids = [el.id for el in collection]
        item.id = max(ids) + 1 if ids else 1
        item.name = "Level"
        item.level = 0
        del scene["mastro_level_list_batch_update"]

        sort_level_list(scene)
        update_all_mastro_plans_level(context)

        for i, el in enumerate(collection):
            if el.id == item.id:
                scene.mastro_level_list_index = i
                break

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
