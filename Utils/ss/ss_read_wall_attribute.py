# function to read the wall parameters:
# if the function is run by the user when in edit mode the wallId is read from 
# context.scene.mastro_attribute_wall_id, else the wall id is updated from the
# wall panel and the wallId used is the one stored in the edge
def read_wall_attribute(context, mesh, edgeIndex, wallSet=None):
    # if wallSet == None:
    #     wall_id = context.scene.mastro_attribute_wall_id
    # else:
    #   wall_id = wallSet
    # projectWalls = context.scene.mastro_wall_name_list

    # index = next((i for i, elem in enumerate(projectWalls) if elem.id == wall_id), None)
    # data = {"wall_id" : wall_id,
    #         "wall_thickness" : projectWalls[index].wallThickness,
    #         "wall_offset" : projectWalls[index].wallOffset
    #         }  
    # return data
    pass