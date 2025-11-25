import bpy 
from bpy.types import Operator

from ..Utils.ss_read_use_attribute import read_use_attribute
from ..Utils.read_wall_attribute import read_wall_attribute
from ..Utils.read_write_bmesh_storey_attribute import read_storey_attribute

# Operator to update the attributes of all the MaStro meshes in the scene        
class OBJECT_OT_Update_Mastro_Mesh_Attributes(Operator):
    bl_idname = "object.update_mastro_mesh_attributes"
    # bl_label = "Update the attributes of all the MaStro meshes in the scene"
    bl_label = "Update"
    bl_options = {'REGISTER', 'UNDO'}
    
    attributeToUpdate: bpy.props.StringProperty(name="Attribute to update")
    
    def execute(self, context):
        
        objs = bpy.data.objects
        # get the current active object
        activeObj = bpy.context.active_object
        if hasattr(activeObj, "type"):
            activeObjMode = activeObj.mode
            
        for obj in objs:
            if (obj is not None and 
                obj.type == 'MESH' and 
                "MaStro object" in obj.data and 
                "MaStro mass" in obj.data):
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
                    # bpy.context.scene.collection.children.link(collection)
                    # print(f"Touching {obj.name}")
                    if obj.name in bpy.context.view_layer.objects:
                        bpy.context.view_layer.objects.active = obj
                        objMode = obj.mode
                        bpy.ops.object.mode_set(mode='OBJECT')
                    
                    mesh = obj.data
                    # faces = context.active_object.data.polygons
                    faces = mesh.polygons
                    if hasattr(mesh, "attributes") and "mastro_typology_id" in mesh.attributes:
                        for face in faces:
                            # print(f"Object {obj.name} face {face.index}")
                            faceIndex = face.index
                            if [i for i in ["all", "floorToFloor", "void"] if i in self.attributeToUpdate]:
                                typology = mesh.attributes["mastro_typology_id"].data[faceIndex].value
                                data = read_use_attribute(context, typologySet = typology)
                                if [i for i in ["all"] if i in self.attributeToUpdate]:
                                    # mesh.attributes["mastro_typology_id"].data[faceIndex].value = data["typology_id"]
                                    mesh.attributes["mastro_list_use_id_A"].data[faceIndex].value = data["use_id_list_A"]
                                    mesh.attributes["mastro_list_use_id_B"].data[faceIndex].value = data["use_id_list_B"]
                                if [i for i in ["all", "floorToFloor"] if i in self.attributeToUpdate]:
                                    mesh.attributes["mastro_list_height_A"].data[faceIndex].value = data["height_A"]
                                    mesh.attributes["mastro_list_height_B"].data[faceIndex].value = data["height_B"]
                                    mesh.attributes["mastro_list_height_C"].data[faceIndex].value = data["height_C"]
                                    mesh.attributes["mastro_list_height_D"].data[faceIndex].value = data["height_D"]
                                    mesh.attributes["mastro_list_height_E"].data[faceIndex].value = data["height_E"]
                                if [i for i in ["all", "void"] if i in self.attributeToUpdate]:
                                    mesh.attributes["mastro_list_void"].data[faceIndex].value = data["void"]
                                    
                            if [i for i in ["all", "numberOfStoreys"] if i in self.attributeToUpdate]:
                                storeys = mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value
                                data = read_storey_attribute(context, mesh, faceIndex, element_type="FACE", storeysSet = storeys)
                                if [i for i in ["all", "numberOfStoreys"] if i in self.attributeToUpdate]:
                                    mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value = data["numberOfStoreys"]
                                    mesh.attributes["mastro_list_storey_A"].data[faceIndex].value = data["storey_list_A"]
                                    mesh.attributes["mastro_list_storey_B"].data[faceIndex].value = data["storey_list_B"]
                            # print(f"Done face {face.index}")
                    # edges = context.active_object.data.edges
                    edges = obj.data.edges
                    if hasattr(mesh, "attributes") and "mastro_wall_id" in mesh.attributes:
                        for edge in edges:
                            edgeIndex = edge.index
                            wall_id = mesh.attributes["mastro_wall_id"].data[edgeIndex].value
                            data = read_wall_attribute(context, mesh, edgeIndex, wallSet = wall_id)
                            if [i for i in ["wall_thickness"] if i in self.attributeToUpdate]:
                                mesh.attributes["mastro_wall_thickness"].data[edgeIndex].value = data["wall_thickness"]
                            elif [i for i in ["wall_offset"] if i in self.attributeToUpdate]:
                                mesh.attributes["mastro_wall_offset"].data[edgeIndex].value = data["wall_offset"]
        
                    if obj.name in bpy.context.view_layer.objects:
                        bpy.ops.object.mode_set(mode=objMode)
                        # If the object was hidden, it is set to hidden again
                        # Also the collection is set to the previous status
                        # In case it has changed
                        if alreadyVisible == False:
                            obj.hide_set(True)
                    if alreadyVisibleCollection == False:
                        collection.hide_viewport = True
                        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
                        # if hasattr(layer_collection, "exclude"):
                        layer_collection.exclude = True
                        # if used_collection == False:
                        #     bpy.context.scene.collection.children.unlink(collection)
                    
                   

        # return the focus to the current active object
        if hasattr(activeObj, "type"):
            bpy.context.view_layer.objects.active = activeObj
            bpy.ops.object.mode_set(mode=activeObjMode)
        return {'FINISHED'}