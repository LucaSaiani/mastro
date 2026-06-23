# FFL is the plan's absolute world Z elevation, so it drives obj.location.z
# directly rather than a Geometry Nodes input - the object itself already
# lives at that height, there is nothing for the modifier to do with it.
# Floor to Floor Height is the only value the GN node group actually needs.
_FFL_DATA_PATH = "mastro_props.mastro_ffl"
_HEIGHT_SOCKET_NAME = "Floor to Floor Height"
_HEIGHT_DATA_PATH = "mastro_props.mastro_floor_to_floor_height"


def _socket_identifier(node_group, socket_name):
    """Resolve a Group Input socket's stable identifier (e.g. 'Socket_3') from
    its display name, since the identifier depends on creation order in the
    node group interface and must not be hardcoded."""
    for item in node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.name == socket_name:
            return item.identifier
    return None


def _add_driver(obj, rna_path, data_path, index=-1):
    fcurve = obj.driver_add(rna_path, index)
    if isinstance(fcurve, list):  # rna_path resolves to an array (e.g. "location")
        fcurve = fcurve[index]
    driver = fcurve.driver
    driver.type = 'AVERAGE'
    var = driver.variables.new()
    var.type = 'SINGLE_PROP'
    target = var.targets[0]
    target.id_type = 'OBJECT'
    target.id = obj
    target.data_path = data_path


def link_all_plan_drivers(obj, modifier):
    """Lock a plan to its level: FFL drives obj.location.z, and Floor to
    Floor Height drives the "Floor to Floor Height" Geometry Nodes input."""
    _add_driver(obj, "location", _FFL_DATA_PATH, index=2)

    identifier = _socket_identifier(modifier.node_group, _HEIGHT_SOCKET_NAME)
    if identifier is None:
        print(f"MaStro Error: socket '{_HEIGHT_SOCKET_NAME}' not found on node group '{modifier.node_group.name}'")
        return
    _add_driver(obj, f'modifiers["{modifier.name}"].properties.inputs.{identifier}.value', _HEIGHT_DATA_PATH)


def unlink_all_plan_drivers(obj, modifier):
    """Remove the drivers added by link_all_plan_drivers."""
    obj.driver_remove("location", 2)

    identifier = _socket_identifier(modifier.node_group, _HEIGHT_SOCKET_NAME)
    if identifier is None:
        return
    obj.driver_remove(f'modifiers["{modifier.name}"].properties.inputs.{identifier}.value')


def _set_plan_height_socket(obj, modifier, value):
    """Write value directly into the Floor to Floor Height modifier input,
    bypassing drivers entirely - used while the plan is unlocked, since
    there is no driver to carry the obj.mastro_props edit through."""
    identifier = _socket_identifier(modifier.node_group, _HEIGHT_SOCKET_NAME)
    if identifier is None:
        return
    modifier.properties.inputs[identifier]["value"] = value


def update_plan_ffl(props_self, context):
    """Update callback for mastro_ffl: while locked the driver already
    pushes the new value into obj.location.z, so this is a no-op; while
    unlocked there is no driver, so the edited value must be written
    directly."""
    if props_self.mastro_lock_to_level:
        return
    obj = props_self.id_data
    obj.location.z = props_self.mastro_ffl


def update_plan_floor_to_floor_height(props_self, context):
    """Update callback for mastro_floor_to_floor_height: while locked the
    driver already pushes the new value into the modifier, so this is a
    no-op; while unlocked there is no driver, so the edited value must be
    written into the modifier input directly."""
    if props_self.mastro_lock_to_level:
        return
    obj = props_self.id_data
    modifier = obj.modifiers.get("MaStro Plan")
    if modifier is None or modifier.node_group is None:
        return
    _set_plan_height_socket(obj, modifier, props_self.mastro_floor_to_floor_height)
