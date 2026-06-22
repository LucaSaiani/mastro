import bpy
from bpy.types import Panel


class PROPERTIES_PT_Mastro_PDF_Sets(Panel):
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "scene"
    bl_label       = "PDF"
    bl_parent_id   = "PROPERTIES_PT_Mastro_Sets"
    bl_options     = {"DEFAULT_CLOSED"}
    bl_order       = 2

    def draw(self, context):
        layout = self.layout
        pp = context.scene.mastro_pdf_props

        if not pp.all_frames:
            layout.label(text="No frames in scene", icon='INFO')
            return

        layout.label(text="Sets")
        row = layout.row()
        row.template_list(
            "PROPERTIES_UL_PDF_Sets", "",
            pp, "pdf_sets",
            pp, "active_set_index",
            rows=5,
        )
        col = row.column(align=True)
        col.operator("mastro.pdf_set_add",       text="", icon='ADD')
        col.operator("mastro.pdf_set_remove",    text="", icon='REMOVE')
        col.separator()
        col.operator("mastro.pdf_set_duplicate", text="", icon='DUPLICATE')
        col.separator()
        col.operator("mastro.pdf_set_move_up",   text="", icon='TRIA_UP')
        col.operator("mastro.pdf_set_move_down", text="", icon='TRIA_DOWN')

        idx = pp.active_set_index
        if not (0 <= idx < len(pp.pdf_sets)):
            return

        layout.label(text="Frames")
        layout.template_list(
            "PROPERTIES_UL_PDF_Frames", "",
            pp, "all_frames",
            pp, "active_frame_index",
            rows=4,
        )

        layout.separator()
        layout.operator("mastro.pdf_set_export", icon='FILE_BLANK')
