# function to read the streets parameters:
# if the function is run by the user when in edit mode the streetId is read from 
# context.scene.attribute_street_id, else the street id is updated from the
# street panel and the streetId used is the one stored in the edge
def read_street_attribute(context, mesh, edgeIndex, streetSet=None):
    if streetSet == None:
        street_id = context.scene.attribute_street_id
    else:
      street_id = streetSet
    projectStreets = context.scene.mastro_street_name_list

    index = next((i for i, elem in enumerate(projectStreets) if elem.id == street_id), None)
    data = {"street_id" : street_id,
            "width" : projectStreets[index].streetWidth,
            "radius" : projectStreets[index].streetRadius
            }  
    return data