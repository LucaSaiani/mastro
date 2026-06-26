"""REFERENCE ONLY - not imported, not registered, not part of the
addon. A working pattern for a collapsible/expandable section inside a
custom Python Node's draw_buttons, confirmed against Blender's own
source (scripts/startup/bl_ui/properties_freestyle.py:473 uses the
exact same row.prop(modifier, "expanded", text="", icon=icon,
emboss=False) trick for its own modifier panels) - not an invention,
the real native mechanism behind every collapsible section drawn this
way in Blender (e.g. the modifier stack).

NOT the same as a Geometry Nodes Group's own NodeTreeInterfacePanel
(the panels you get when editing a Node Group's Input/Output/Panel
interface) - that's a property of bNodeTree.interface (see
BKE_node_tree_interface.hh), grouping declared SOCKETS, and has no
equivalent for a plain custom bpy.types.Node's own sockets (created
directly via self.inputs.new(...) in init(), never through an
interface layer at all). This pattern only groups PLAIN PROPERTIES
drawn inside draw_buttons (FloatProperty/BoolProperty/StringProperty/
etc., not sockets) - draw_buttons is always drawn above every socket
regardless (confirmed against node_draw.cc), so this can never
intersperse with the socket list itself.

`bpy.types.NodePanel` (seen proposed elsewhere, with a `bl_node_type`
class attribute) does NOT exist anywhere in Blender's source (checked:
no hit in scripts/ or source/blender/makesrna/) - that earlier
suggestion was a plausible-looking invention, not a real API.

Worth revisiting if a future node needs to group several PURE
PROPERTIES (not sockets) into expandable sections - e.g. an "Advanced"
box that's collapsed by default. Not directly useful for Edit Header's
own String/Background Colour/Text Colour, which are all sockets, not
plain properties - this pattern can't touch those.
"""

import bpy


class MyCustomNode(bpy.types.Node):
    bl_idname = 'MyCustomNodeType'
    bl_label = "Custom Node con Pannelli"
    bl_icon = 'NODE'

    # Boolean "is this section open" flags - one per collapsible box.
    panel_1_open: bpy.props.BoolProperty(default=False)
    panel_2_open: bpy.props.BoolProperty(default=False)

    prop_a: bpy.props.FloatProperty(name="Parametro A")
    prop_b: bpy.props.IntProperty(name="Parametro B")
    prop_c: bpy.props.StringProperty(name="Note")

    def draw_buttons(self, context, layout):
        box1 = layout.box()
        row1 = box1.row(align=True)
        icon_p1 = 'TRIA_DOWN' if self.panel_1_open else 'TRIA_RIGHT'
        # emboss=False + icon=TRIA_DOWN/TRIA_RIGHT is the actual native
        # trick (see this file's own module docstring) - the row.prop
        # call both draws the toggle AND flips panel_1_open when clicked,
        # no separate operator needed.
        row1.prop(self, "panel_1_open", text="Impostazioni Principali", icon=icon_p1, emboss=False)
        if self.panel_1_open:
            col1 = box1.column(align=True)
            col1.separator()
            col1.prop(self, "prop_a")
            col1.prop(self, "prop_b")

        box2 = layout.box()
        row2 = box2.row(align=True)
        icon_p2 = 'TRIA_DOWN' if self.panel_2_open else 'TRIA_RIGHT'
        row2.prop(self, "panel_2_open", text="Opzioni Avanzate", icon=icon_p2, emboss=False)
        if self.panel_2_open:
            col2 = box2.column(align=True)
            col2.separator()
            col2.prop(self, "prop_c")
