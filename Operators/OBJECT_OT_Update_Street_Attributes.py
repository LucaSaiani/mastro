import bpy 
from bpy.types import Operator

from ..Utils.read_street_attribute import read_street_attribute
# Operator to update the attributes of all the MaStro streets in the scene        
class OBJECT_OT_update_all_MaStro_street_attributes(Operator):
    bl_idname = "object.update_all_mastro_street_attributes"
    bl_label = "Update"
    bl_options = {'REGISTER', 'UNDO'}
    
    attribute_to_update: bpy.props.StringProperty(name="Attribute to update")
    
    def execute(self, context):
        objs = bpy.data.objects
        # get the current active object
        activeObj = bpy.context.active_object
        if hasattr(activeObj, "type"):
            activeObjMode = activeObj.mode
            
        for obj in objs:
            if obj is not None and obj.type == 'MESH' and "MaStro object" in obj.data and "MaStro street" in obj.data:
                # it is necessary to set the object to visibile in order to make it active
                if obj.visible_get():
                    alreadyVisible = True
                else:
                    alreadyVisible = False
                    obj.hide_set(False)
                
                # check if the collection is visible or not
                collections = obj.users_collection
                used_collection = False
                alreadyVisibleCollection = False
                for collection in collections:
                    if not collection.hide_viewport:
                        used_collection = True
                        alreadyVisibleCollection = True
                        break
                    else:
                        collection.hide_viewport = False
                        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
                        if hasattr(layer_collection, "exclude"):
                            layer_collection.exclude = False
                            used_collection = True
                            break
                # Only the linked objects are updated
                if used_collection == True:
                    bpy.context.view_layer.objects.active = obj
                    mesh = obj.data
                    objMode = obj.mode
                    bpy.ops.object.mode_set(mode='OBJECT')
                    edges = context.active_object.data.edges
                    for edge in edges:
                        edgeIndex = edge.index
                        street_id = mesh.attributes["mastro_street_id"].data[edgeIndex].value
                        data = read_street_attribute(context, mesh, edgeIndex, streetSet = street_id)
                        if [i for i in ["width"] if i in self.attribute_to_update]:
                            mesh.attributes["mastro_street_width"].data[edgeIndex].value = data["width"]/2
                        elif [i for i in ["radius"] if i in self.attribute_to_update]:
                            mesh.attributes["mastro_street_radius"].data[edgeIndex].value = data["radius"]
                    bpy.ops.object.mode_set(mode=objMode)
                    
                    # If the object was hidden, it is set to hidden again
                    # Also the collection is set to the previous status
                    # In case it has changed
                    if alreadyVisible == False:
                        obj.hide_set(True)
                    if alreadyVisibleCollection == False:
                        collection.hide_viewport = True
                        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
                        layer_collection.exclude = True

        # return the focus to the current active object
        if hasattr(activeObj, "type"):
            bpy.context.view_layer.objects.active = activeObj
            bpy.ops.object.mode_set(mode=activeObjMode)
        return {'FINISHED'}