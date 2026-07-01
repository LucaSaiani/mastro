import bpy
import bmesh
from bpy.types import Panel

class VIEW3D_PT_Mastro_Street(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Street"
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                # context.selected_objects != [] and
                context.object.type == "MESH" and
                "MaStro object" in context.object.data and
                "MaStro street" in context.object.data)

    def draw(self, context):
        obj = context.object
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode == "OBJECT":
                scene = context.scene

                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False  # No animation.

                row = layout.row(align=True)

                # layout.prop(obj.mastro_props, "mastro_option_attribute", text="Option")
                # layout.prop(obj.mastro_props, "mastro_phase_attribute", text="Phase")

            elif mode == "EDIT":
                scene = context.scene

                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False  # No animation.

                select_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)

                if select_mode[1] == True: #we are selecting edges
                    row = layout.row(align=True)
                    row.prop(context.scene, "mastro_street_names", text="Street Type")

                    active = _active_edge(context)
                    if active is not None:
                        col = layout.column()
                        col.use_property_split = True
                        col.use_property_decorate = False
                        col.row().prop(scene, "mastro_street_sector_enum_A", text="Junction A", expand=True)
                        col.row().prop(scene, "mastro_street_sector_enum_B", text="Junction B", expand=True)


def _active_edge(context):
    obj = context.active_object
    if not (obj and obj.type == "MESH" and obj.mode == 'EDIT'):
        return None
    try:
        bm = bmesh.from_edit_mesh(obj.data)
    except Exception:
        return None
    active = bm.select_history.active
    return active if isinstance(active, bmesh.types.BMEdge) else None
