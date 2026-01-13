import bpy 
from bpy.types import Operator

from ...Utils.get_preferences  import get_prefs

# to open a new window, the preferences window 
# is opened and then the area type is changed to text editor
def openTextEditor(text):
    bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
    window = bpy.context.window_manager.windows[-1]
    area = window.screen.areas[0]
    area.type = "TEXT_EDITOR"
    area.spaces[0].show_region_header = False
    area.spaces[0].show_region_footer = False
    area.spaces[0].show_line_numbers = False
    area.spaces[0].show_syntax_highlight = False
    area.spaces[0].show_word_wrap = True
    area.spaces[0].text = text


    
        
class NODE_OT_Sticky_Note(Operator):
    bl_idname = "node.sticky_note"
    bl_label = "sticky Note"
    bl_description = "MaStro Sticky Note"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        #get the list of all selected nodes
        node_tree = bpy.context.space_data.edit_tree
        if node_tree:
            activeNode = node_tree.nodes.active
            is_custom_note = False
            if activeNode and hasattr(activeNode, "mastro_sticky_note_props"):
                is_custom_note = activeNode.mastro_sticky_note_props.customNote
                
            # edit existing note
            if activeNode and activeNode.select and is_custom_note:
                postIt = activeNode
                if hasattr(postIt, 'text') and postIt.text:
                    textName = postIt.text.name
                    note_text = bpy.data.texts[textName]
                    openTextEditor(note_text)
                # else:
                #     self.report({'WARNING'}, "Selected node is a custom note but has no linked text data.")
                    # return {'CANCELLED'} # Or handle gracefully
            # create a new note
            else:
                postIt = node_tree.nodes.new("NodeFrame")
                # postIt.select = False
                postIt.name = "MaStro note"
                postIt.label = "Note"
                postIt.mastro_sticky_note_props.customNote = True
           
                postIt.use_custom_color = True
                prefs = get_prefs()
                postIt.color = prefs.noteColor
                postIt.label_size = prefs.noteSize
                postIt.shrink = False
                if activeNode and activeNode.select:
                    postIt.location = activeNode.location
                    postIt.location.y = activeNode.height + 20
                else:
                    postIt.location = node_tree.view_center
                postIt.width = 200
                postIt.height = 200
                note_text = bpy.data.texts.new("MaStro note")
                note_text.use_fake_user = False
      
                postIt.text = bpy.data.texts[note_text.name]
                openTextEditor(note_text)
            
        return {'FINISHED'}