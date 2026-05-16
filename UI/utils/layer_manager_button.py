def draw_layer_manager_header_button(self, context):
    """Replaces TOPBAR_HT_upper_bar.draw_right to add the view-layer manager controls."""
    layout = self.layout

    window = context.window
    screen = context.screen

    if not screen.show_statusbar:
        layout.template_reports_banner()
        layout.template_running_jobs()

    layout.template_ID(window, "scene", new="scene.new", unlink="scene.delete")

    row = layout.row(align=True)
    row.popover(
        panel="LAYER_MANAGER_PT_Popup",
        text="",
        icon='RENDER_RESULT',
    )
    row.prop(context.window.view_layer, "name", text="")
    row.operator("layer_manager.add_layer_popup", text="", icon='DUPLICATE')
    row.operator("scene.view_layer_remove", icon="X", text="")
