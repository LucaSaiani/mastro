from .light_source_guard import register as register_light_source_guard, unregister as unregister_light_source_guard


def register():
    register_light_source_guard()


def unregister():
    unregister_light_source_guard()
