'''Block: function to update depth of the building accordingly to the assigned number of storeys'''
# def update_mesh_edge_attributes_depth(context, mesh, edgeIndex, depthSet = None):
def read_depth_attribute(context, depthSet = None):

    # typology_id = mesh.attributes["mastro_typology_id_EDGE"].data[edgeIndex].value
    # projectUses = context.scene.mastro_use_name_list

    # if the function is run once the user updates the depth of the building,
    # the value is read from context.scene.mastro_attribute_block_depth.
    # Else the function is run because the user is updating the depth and
    # in this case the value used is the one stored in each edge of the mesh
    if depthSet == None:
        blockDepth = context.scene.mastro_attribute_block_depth
        if blockDepth == 0:
            blockDepth = 18
    else:
        blockDepth = depthSet
    
    data = {"blockDepth" : float(blockDepth)
            }
    return data