import bpy

street_attribute_set = [
            {
            "attr" :  "mastro_street_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_street_width",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 8
            },
            {
            "attr" :  "mastro_street_radius",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 16
            },
            {
            "attr" : "mastro_custom_vertex",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "POINT",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_edge",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_face",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            # Per-edge intersection-sector type at each of the edge's two ends (0=double
            # fillet, 1/2=fillet on one side with an offset on the other - which side is
            # which has no absolute meaning, the user picks visually in the UI). Plain INT,
            # not digit-packed: an edge always has exactly two ends, so there's no list to
            # pack. _A is the type at edge.vertices[0], _B at edge.vertices[1] - this native
            # Blender vertex order must stay stable through the GN node group for the value
            # to mean the same end on both sides (verify in practice once the GN side reads
            # these attributes - not yet confirmed whether MaStro Street Elements' internal
            # operations preserve edge vertex order throughout).
            "attr" : "mastro_street_sector_type_A",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_street_sector_type_B",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            }
]

def add_street_attributes(obj):
    # obj.mastro_props['mastro_option_attribute'] = 1
    # obj.mastro_props['mastro_phase_attribute'] = 1
    mesh = obj.data
    mesh["MaStro object"] = True
    mesh["MaStro street"] = True
    
    street_id = bpy.context.scene.mastro_street_name_list_index
    width = bpy.context.scene.mastro_street_name_list[street_id].streetWidth
    radius = bpy.context.scene.mastro_street_name_list[street_id].streetRadius
    
    for a in street_attribute_set:
        try:
            mesh.attributes[a["attr"]]
        except:
            if a["attr_domain"] is None: # to set custom attributes to the object, not to vertex, edge or face
                obj[a["attr"]] = a["attr_default"]
            else:
                mesh.attributes.new(name=a["attr"], type=a["attr_type"], domain=a["attr_domain"])
                if a["attr_domain"] == 'EDGE':
                    attribute = mesh.attributes[a["attr"]].data.items()
                    for edge in mesh.edges:
                        index = edge.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                if a["attr"] == "mastro_street_id":
                                    mesh_attribute[1].value = street_id
                                elif a["attr"] == "mastro_street_width":
                                    mesh_attribute[1].value = width
                                elif a["attr"] == "mastro_street_radius":
                                    mesh_attribute[1].value = radius
                                break