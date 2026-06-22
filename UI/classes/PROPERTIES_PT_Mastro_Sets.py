from bpy.types import Panel


class PROPERTIES_PT_Mastro_Sets(Panel):
    """Container for the set-based sub-panels (Level Sets, Camera Sets,
    PDF Sets), which all share the same list-of-sets + members pattern."""
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Sets"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4

    def draw(self, context):
        pass
