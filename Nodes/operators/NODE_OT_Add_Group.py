import bpy
from bpy.types import Operator


class NODE_OT_Mastro_Add_Group(Operator):
    """Add a MaStro node group to the active node tree"""
    bl_idname = "node.mastro_add_group"
    bl_label  = "Add MaStro Group"
    bl_options = {'REGISTER', 'UNDO'}

    group_name: bpy.props.StringProperty()

    def execute(self, context):
        ng = bpy.data.node_groups.get(self.group_name)
        if ng is None:
            self.report({'WARNING'}, f"Node group '{self.group_name}' not found")
            return {'CANCELLED'}
        tree = context.space_data.edit_tree
        if tree is None:
            return {'CANCELLED'}
        # Use the right node type for the current editor (GN vs Shader)
        node_type = 'ShaderNodeGroup' if ng.type == 'SHADER' else 'GeometryNodeGroup'
        node = tree.nodes.new(node_type)
        node.node_tree = ng
        node.location = context.space_data.cursor_location
        # Deselect all, select the new node so it follows the cursor
        for n in tree.nodes:
            n.select = False
        node.select = True
        tree.nodes.active = node
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        return {'FINISHED'}
