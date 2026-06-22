import bpy
from bpy.types import UIList


class PROPERTIES_UL_Level_Set_Members(UIList):
    """UIList of every level in the scene, with a checkbox to toggle its
    membership in the active level set.

    The membership checkbox is a real toggle prop (item.in_active_set,
    backed by a get/set pair in property_classes_levels.py) rather than an
    operator button, so Blender's native click-drag over several rows can
    assign/unassign multiple levels in one gesture.

    The "assigned only" filter is exposed as a button next to the list in
    PROPERTIES_PT_Mastro_Level_Sets instead of Blender's own filter row, so
    that row is suppressed entirely (no search box, no sort buttons).
    """

    use_filter_show: bpy.props.BoolProperty(default=False)

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            scene = context.scene
            level_sets = scene.mastro_level_set_list
            idx = scene.mastro_level_set_list_index
            active_set = level_sets[idx] if 0 <= idx < len(level_sets) else None

            row = layout.row(align=True)
            row.label(text=f"Id: {item.id}")
            row.label(text=item.name)

            sub = row.row(align=True)
            sub.alignment = 'RIGHT'
            if active_set is not None:
                # The "All Levels" set (id 0) always contains every level;
                # show it checked and disabled rather than toggleable.
                is_all_levels = active_set.id == 0
                check_icon = 'CHECKBOX_HLT' if item.in_active_set else 'CHECKBOX_DEHLT'
                s = sub.row(align=True)
                s.enabled = not is_all_levels
                s.prop(item, "in_active_set", text="", icon=check_icon, emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        scene = context.scene
        level_sets = scene.mastro_level_set_list
        idx = scene.mastro_level_set_list_index
        active_set = level_sets[idx] if 0 <= idx < len(level_sets) else None

        filter_on = scene.mastro_level_set_filter_members_only and active_set and active_set.id != 0
        if filter_on:
            member_ids = {el.level_id for el in active_set.levels}
            flt_flags = [
                self.bitflag_filter_item if item.id in member_ids else 0
                for item in items
            ]
        else:
            flt_flags = [self.bitflag_filter_item] * len(items)

        return flt_flags, []
