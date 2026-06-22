from bpy.types import UIList


class PROPERTIES_UL_Level_Set_Members(UIList):
    """UIList of every level in the scene, with a checkbox to toggle its
    membership in the active level set."""

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
                if active_set.id == 0:
                    sub.label(text="", icon='CHECKBOX_HLT')
                else:
                    in_set = any(el.level_id == item.id for el in active_set.levels)
                    check_icon = 'CHECKBOX_HLT' if in_set else 'CHECKBOX_DEHLT'
                    op = sub.operator(
                        "mastro_level_set_list.toggle_level",
                        text="", icon=check_icon, emboss=False,
                    )
                    op.level_id = item.id
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []

    def draw_filter(self, context, layout):
        pass
