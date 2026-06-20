import bpy


# add MaStro album parenting entries to the Ctrl+P / Alt+P menu
def add_parent_menu(self, context):
    self.layout.separator()
    self.layout.operator("object.mastro_parent_to_album", icon='LINKED')
    self.layout.operator("object.mastro_unparent_from_album", icon='UNLINKED')


def register():
    bpy.types.VIEW3D_MT_object_parent.append(add_parent_menu)


def unregister():
    bpy.types.VIEW3D_MT_object_parent.remove(add_parent_menu)
