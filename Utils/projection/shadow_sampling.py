def _build_silhouette_edges(mesh_objs, sun_visible_faces):
    """Return the set of sun-silhouette edge keys and an edge-info dict.

    A silhouette edge is shared by exactly one sun-visible face (boundary
    between lit and dark regions as seen from the sun).
    """
    edge_face_count = {}
    edge_info       = {}
    for obj in mesh_objs:
        me = obj.data
        for poly in me.polygons:
            if (obj.name, poly.index) not in sun_visible_faces:
                continue
            n = len(poly.vertices)
            for i in range(n):
                vi_a = poly.vertices[i]
                vi_b = poly.vertices[(i + 1) % n]
                key  = (obj.name, min(vi_a, vi_b), max(vi_a, vi_b))
                edge_face_count[key] = edge_face_count.get(key, 0) + 1
                edge_info[key]       = (vi_a, vi_b, obj)
    return {k for k, cnt in edge_face_count.items() if cnt == 1}, edge_info
