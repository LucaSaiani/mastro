import bpy
import sys
from ..utils.node_utils import create_new_nodegroup, create_socket
from ...Utils.mastro_cad.drawing_materials import ensure_layer_material

GN_GROUP_NAME = "MaStro Drawing"
GN_CHAIN_NAME = ".MaStro Layer Setup"


def _link_chain_ng_from_mastro():
    """Delegate node linking to mastro's add_nodes() via sys.modules.

    Uses mastro's own PREFS_KEY to locate the module regardless of whether
    the addon is installed as a development extension or a release package.
    """
    # mastro sets PREFS_KEY = __package__ at startup — use it to find the module.
    mastro = None
    for key, mod in sys.modules.items():
        if hasattr(mod, 'PREFS_KEY') and hasattr(mod, 'Utils') and 'mastro' in key.lower():
            mastro = mod
            break
    if mastro is None:
        print("MaStro Drawing: MaStro addon not loaded.")
        return
    try:
        mastro.Utils.add_nodes.add_nodes()
    except Exception as e:
        print(f"MaStro Drawing: add_nodes() failed: {e}")

# Layout constants — main group
X_ATTR  = -700
X_EQ    = -450
X_SEP   = -200
X_CHAIN =   80
X_JOIN  =  380
X_OUT   =  560
Y_STEP  = -260


def _add_chain_instance(nodes, links, chain_ng, geom_out, join_in, x, y,
                        material=None, scale_out=None, layer_id=None):
    n = nodes.new('GeometryNodeGroup')
    n.node_tree = chain_ng
    n.location  = (x, y)
    if layer_id is not None:
        n.label = f"layer_{layer_id}"
    links.new(geom_out,                   n.inputs['Geometry'])
    links.new(n.outputs['Grease Pencil'], join_in)
    if material is not None:
        n.inputs['Material'].default_value = material
    if scale_out is not None and 'Scale' in n.inputs:
        links.new(scale_out, n.inputs['Scale'])
    return n


def build_drawing_gn(layers, scene=None):
    """Build or rebuild the MaStro Drawing node group.

    layers: list of (layer_id: int, name: str) tuples.
    scene:  bpy.types.Scene, used to resolve layer materials.

    The .MaStro Layer Setup sub-group is a linked asset from mastro.blend —
    it is never built by code. If it is not present, the build is aborted.
    """
    chain_ng = bpy.data.node_groups.get(GN_CHAIN_NAME)
    if chain_ng is None:
        _link_chain_ng_from_mastro()
        chain_ng = bpy.data.node_groups.get(GN_CHAIN_NAME)
    if chain_ng is None:
        print(f"MaStro Drawing: '{GN_CHAIN_NAME}' not found in mastro.blend.")
        return None

    if GN_GROUP_NAME in bpy.data.node_groups:
        ng = bpy.data.node_groups[GN_GROUP_NAME]
        ng.nodes.clear()
        ng.interface.clear()
    else:
        ng = bpy.data.node_groups.new(name=GN_GROUP_NAME, type='GeometryNodeTree')

    create_socket(ng, in_out='INPUT',  socket_type='NodeSocketGeometry', socket_name='Geometry')
    create_socket(ng, in_out='OUTPUT', socket_type='NodeSocketGeometry', socket_name='Geometry')


    nodes = ng.nodes
    links = ng.links

    n_layers = len(layers)
    total_h  = (n_layers - 1) * Y_STEP

    n_in  = nodes.new('NodeGroupInput')
    n_out = nodes.new('NodeGroupOutput')
    n_join = nodes.new('GeometryNodeJoinGeometry')

    n_in.location   = (X_ATTR - 300, total_h / 2)
    n_join.location = (X_JOIN, total_h / 2)
    n_out.location  = (X_OUT,  total_h / 2)

    links.new(n_join.outputs['Geometry'], n_out.inputs['Geometry'])

    # Integer node for scale — one driver updates all objects at once.
    n_scale = nodes.new('FunctionNodeInputInt')
    n_scale.label    = "Scale"
    n_scale.integer  = 100
    n_scale.location = (X_ATTR - 300, total_h / 2 - 150)
    scale_out = n_scale.outputs[0]

    # Set initial value from scene if available.
    if scene is not None:
        n_scale.integer = scene.mastro_cad_drawing_scale

    if n_layers == 0:
        links.new(n_in.outputs['Geometry'], n_out.inputs['Geometry'])
        return ng

    # Single Named Attribute node shared by all Compare nodes
    n_attr = nodes.new('GeometryNodeInputNamedAttribute')
    n_attr.data_type = 'INT'
    n_attr.inputs['Name'].default_value = 'mastro_drawing_layer'
    n_attr.location = (X_ATTR, total_h / 2)

    current_geom = n_in.outputs['Geometry']

    for i, (layer_id, _layer_name) in enumerate(layers[:-1]):
        y = i * Y_STEP

        n_eq = nodes.new('FunctionNodeCompare')
        n_eq.data_type = 'INT'
        n_eq.operation = 'EQUAL'
        n_eq.inputs['B'].default_value = layer_id
        n_eq.location = (X_EQ, y - 60)

        n_sep = nodes.new('GeometryNodeSeparateGeometry')
        n_sep.domain   = 'EDGE'
        n_sep.location = (X_SEP, y)

        links.new(n_attr.outputs['Attribute'], n_eq.inputs['A'])
        links.new(current_geom,                n_sep.inputs['Geometry'])
        links.new(n_eq.outputs['Result'],      n_sep.inputs['Selection'])

        mat = ensure_layer_material(scene, layer_id) if scene else None
        _add_chain_instance(nodes, links, chain_ng,
                            n_sep.outputs['Selection'],
                            n_join.inputs['Geometry'],
                            X_CHAIN, y, material=mat, scale_out=scale_out,
                            layer_id=layer_id)

        current_geom = n_sep.outputs['Inverted']

    # Last layer: remaining geometry
    last_id  = layers[-1][0]
    last_mat = ensure_layer_material(scene, last_id) if scene else None
    _add_chain_instance(nodes, links, chain_ng,
                        current_geom,
                        n_join.inputs['Geometry'],
                        X_CHAIN, (n_layers - 1) * Y_STEP, material=last_mat, scale_out=scale_out,
                        layer_id=last_id)

    return ng


def rebuild_drawing_gn(scene):
    """Rebuild the node group from the current scene layer list."""
    layers = [(l.layer_id, l.name) for l in scene.mastro_cad_layers]
    build_drawing_gn(layers, scene=scene)
