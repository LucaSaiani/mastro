from bpy.types import Panel


class PROPERTIES_PT_Mastro_3D_Building(Panel):
    """Container for the 3D building geometry sub-panels (Typology, Block,
    Building, Wall, Floor) - the 3D counterpart of "Drawing" (2D)."""
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Building"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    def draw(self, context):
        pass
