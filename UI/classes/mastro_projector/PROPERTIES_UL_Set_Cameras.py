import bpy
from bpy.types import UIList


class PROPERTIES_UL_Set_Cameras(UIList):
    bl_idname = "PROPERTIES_UL_Set_Cameras"

    use_filter_show: bpy.props.BoolProperty(default=True)

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        cam_name = item.camera_name
        cam_obj  = bpy.data.objects.get(cam_name)
        if cam_obj is None or cam_obj.data is None:
            layout.label(text=cam_name, icon='ERROR')
            return

        ssp        = context.scene.mastro_projector_props
        idx        = ssp.active_set_index
        active_set = ssp.camera_sets[idx] if 0 <= idx < len(ssp.camera_sets) else None
        props      = cam_obj.data.mastro_projector_cl

        row = layout.row(align=True)

        # Column 1: camera type icon
        row.label(text="", icon='OUTLINER_OB_CAMERA')

        # Column 2: camera name
        row.label(text=cam_name)

        # Right: membership checkbox + render on/off
        sub = row.row(align=True)
        sub.alignment = 'RIGHT'

        if active_set and not active_set.is_default:
            in_set     = any(it.camera_name == cam_name for it in active_set.cameras)
            check_icon = 'CHECKBOX_HLT' if in_set else 'CHECKBOX_DEHLT'
            op = sub.operator(
                "mastro.camera_set_toggle_camera",
                text="", icon=check_icon, emboss=False,
            )
            op.camera_name = cam_name
        else:
            s = sub.row(align=True)
            s.enabled = False
            s.label(text="", icon='CHECKBOX_HLT')

        render_icon = 'RESTRICT_RENDER_OFF' if props.active_for_batch else 'RESTRICT_RENDER_ON'
        sub.prop(props, "active_for_batch", text="", icon=render_icon, emboss=False)

    def draw_filter(self, context, layout):
        ssp        = context.scene.mastro_projector_props
        idx        = ssp.active_set_index
        active_set = ssp.camera_sets[idx] if 0 <= idx < len(ssp.camera_sets) else None
        is_default = active_set.is_default if active_set else True

        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.enabled = not is_default
        sub.prop(ssp, "filter_set_members_only", text="",
                 icon='FILTER', toggle=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "use_filter_sort_alpha", text="", icon='SORTALPHA')
        row.prop(self, "use_filter_sort_reverse", text="", icon='SORT_DESC')

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags    = []
        flt_neworder = []

        ssp        = context.scene.mastro_projector_props
        idx        = ssp.active_set_index
        active_set = ssp.camera_sets[idx] if 0 <= idx < len(ssp.camera_sets) else None

        filter_on = ssp.filter_set_members_only and active_set and not active_set.is_default
        if filter_on:
            member_names = {it.camera_name for it in active_set.cameras}
            flt_flags = [
                self.bitflag_filter_item if item.camera_name in member_names else 0
                for item in items
            ]
        else:
            flt_flags = [self.bitflag_filter_item] * len(items)

        if self.filter_name:
            name_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, items, "camera_name",
            )
            flt_flags = [a & b for a, b in zip(flt_flags, name_flags)]

        if self.use_filter_sort_alpha:
            flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(
                items, "camera_name"
            )

        return flt_flags, flt_neworder
