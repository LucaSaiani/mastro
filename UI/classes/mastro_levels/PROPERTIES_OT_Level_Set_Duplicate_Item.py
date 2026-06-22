from bpy.types import Operator


class PROPERTIES_OT_Level_Set_Duplicate_Item(Operator):
    """Duplicate the selected level set.

    Unlike remove/toggle, duplicating the "All Levels" set (id 0) is not
    blocked. Since its membership is virtual (derived live from
    mastro_level_list, not stored in `levels`), the duplicate is given an
    explicit snapshot of all current level ids instead of an empty
    `levels` collection, so it behaves as a normal, editable set.
    """
    bl_idname = "mastro_level_set_list.duplicate_item"
    bl_label = "Duplicate level set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        collection = scene.mastro_level_set_list
        index = scene.mastro_level_set_list_index

        if not collection or index < 0 or index >= len(collection):
            return {'CANCELLED'}

        src = collection[index]
        dst = collection.add()
        ids = [el.id for el in collection]
        dst.id = max(ids) + 1 if ids else 1
        dst.name = src.name + " Copy"
        if src.id == 0:
            # src.levels is empty (membership is virtual); snapshot the
            # real level list instead so the duplicate isn't empty.
            for level in scene.mastro_level_list:
                dst.levels.add().level_id = level.id
        else:
            for item in src.levels:
                dst.levels.add().level_id = item.level_id

        scene.mastro_level_set_list_index = len(collection) - 1

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
