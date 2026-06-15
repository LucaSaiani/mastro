def draw_console_header_mastro_button(self, context):
    pp = context.scene.mastro_print_props
    idx = pp.active_set_index
    set_name = pp.print_sets[idx].name if 0 <= idx < len(pp.print_sets) else ""

    self.layout.operator("object.mastro_print_configured", text=f"Print Schedule: {set_name}", icon='CONSOLE')
    self.layout.operator("object.mastro_print_config", text="", icon='PREFERENCES')
    self.layout.prop(pp, "scan_scope", text="")