import bpy
from bpy.types import UIList


class PROPERTIES_UL_PDF_Frames(UIList):
    bl_idname = "PROPERTIES_UL_PDF_Frames"

    use_filter_show: bpy.props.BoolProperty(default=False)

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        frame_name = item.frame_name
        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        active_set = pp.pdf_sets[idx] if 0 <= idx < len(pp.pdf_sets) else None

        row = layout.row(align=True)
        row.label(text="", icon='FILE')
        row.label(text=frame_name)

        sub = row.row(align=True)
        sub.alignment = 'RIGHT'
        if active_set is not None:
            # item.in_active_set is a real toggle prop (get/set backed by
            # the active set's `frames` collection), not an operator
            # button, so Blender's native click-drag over several rows can
            # assign/unassign multiple frames in one gesture.
            check_icon = 'CHECKBOX_HLT' if item.in_active_set else 'CHECKBOX_DEHLT'
            sub.prop(item, "in_active_set", text="", icon=check_icon, emboss=False)

    def draw_filter(self, context, layout):
        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        active_set = pp.pdf_sets[idx] if 0 <= idx < len(pp.pdf_sets) else None

        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.enabled = active_set is not None
        sub.prop(pp, "filter_set_members_only", text="",
                 icon='FILTER', toggle=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "use_filter_sort_alpha", text="", icon='SORTALPHA')
        row.prop(self, "use_filter_sort_reverse", text="", icon='SORT_DESC')

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = [self.bitflag_filter_item] * len(items)
        flt_neworder = []

        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        active_set = pp.pdf_sets[idx] if 0 <= idx < len(pp.pdf_sets) else None

        if pp.filter_set_members_only and active_set:
            member_names = {it.frame_name for it in active_set.frames}
            flt_flags = [
                self.bitflag_filter_item if item.frame_name in member_names else 0
                for item in items
            ]

        if self.filter_name:
            name_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, items, "frame_name",
            )
            flt_flags = [a & b for a, b in zip(flt_flags, name_flags)]

        if self.use_filter_sort_alpha:
            flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(
                items, "frame_name"
            )

        return flt_flags, flt_neworder
