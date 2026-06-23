from bpy.types import Panel


class VIEW3D_PT_Mastro_Plan(Panel):
    """VIEW3D sidebar panel for plan objects.

    Shows FFL (with its bottom level's name) and floor to floor Height -
    both read-only while locked to a level, since they are then driven by
    drivers (see Utils.mastro_arch.plan_drivers) kept in sync with the
    level list by update_plan_attributes whenever a level changes - and
    editable once unlocked, the edits going straight to obj.location.z /
    the Geometry Nodes modifier input instead (see plan_drivers' update_*
    callbacks).

    The lock state itself is shown/toggled at the bottom: a single "Unlock"
    button while locked, or "Lock to Active Level" plus a per-level dropdown
    while unlocked - never a plain checkbox, since (un)locking must also
    add/remove the drivers above, not just flip a bool (see the dedicated
    operators in OBJECT_OT_Mastro_Plan_Lock_To_Level).
    """
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Plan"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == "MESH" and
                "MaStro object" in context.object.data and
                "MaStro plan" in context.object.data)

    def draw(self, context):
        obj = context.object
        scene = context.scene
        props = obj.mastro_props

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        level = next((lvl for lvl in scene.mastro_level_list
                      if lvl.id == props.mastro_bottom_level_id), None)
        level_name = level.name if level is not None else ""

        col = layout.column()
        col.enabled = not props.mastro_lock_to_level

        row = col.row(align=True)
        row.prop(props, "mastro_ffl", text="FFL")
        row.label(text=level_name)

        col.prop(props, "mastro_floor_to_floor_height", text="Height")

        row = layout.row(align=True)
        if props.mastro_lock_to_level:
            row.operator("object.mastro_plan_unlock_from_level",
                          text="Unlock", icon='LOCKED')
        else:
            row.operator("object.mastro_plan_lock_to_level",
                          text="Lock to Active Level")
            row.menu("MASTRO_MT_Plan_Lock_To_Level", text="", icon='DOWNARROW_HLT')

        col = layout.column(align=True)
        # Disabled while unlocked: with no level to exclude/derive from,
        # there is nothing for the operator to skip duplicating onto.
        col.enabled = props.mastro_lock_to_level
        # link_mesh has no UI by default (only the F9 redo panel after running
        # the operator), so it's persisted on window_manager instead and fed
        # into the operator call here - keeps the checkbox below always
        # visible/editable before running, not just after.
        col.operator("object.mastro_plan_duplicate_to_levels",
                      text="Duplicate to Level Set").link_mesh = context.window_manager.mastro_plan_duplicate_link_mesh
        col.prop(context.window_manager, "mastro_plan_duplicate_link_mesh")
