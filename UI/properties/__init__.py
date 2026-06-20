
from .property_classes import mastro_CL_name_with_id
from .property_classes_gn import mastro_CL_Sticky_Note
from .property_classes_constraints import mastro_CL_constraint_XY_settings
from .property_classes_projector import (mastro_CL_projector_properties,
                                         mastro_CL_projector_batch_item,
                                         mastro_CL_camera_set_item,
                                         mastro_CL_camera_set,
                                         mastro_CL_projector_scene_props,
)
from .property_classes_layer import (mastro_CL_layer_slot,
                                     mastro_CL_layer_manager_props,
)
from .property_classes_street import mastro_CL_street_name_list
from .property_classes_pdf import (mastro_CL_pdf_frame_item,
                                   mastro_CL_pdf_set,
                                   mastro_CL_pdf_scene_props,
)
from .property_classes_arch import (mastro_CL_addon_properties,
                                    mastro_CL_floor_name_list,
                                    mastro_CL_wall_name_list,
                                    mastro_CL_typology_uses_name_list,
                                    mastro_CL_use_name_list,
                                    mastro_CL_typology_name_list,
                                    mastro_CL_building_name_list,
                                    mastro_CL_block_name_list,
                                    mastro_CL_obj_typology_uses_name_list,
)
from .property_classes_custom_properties import (mastro_CL_custom_property_name_list,
                                                  mastro_CL_custom_property_string_name_list,
)
from .property_classes_cad import (mastro_CL_cad_pen,
                                   mastro_CL_cad_dash_pattern,
                                   mastro_CL_cad_layer,
)
from .property_classes_print import (mastro_CL_print_set_param,
                                      mastro_CL_print_set,
                                      mastro_CL_print_scene_props,
)
from .property_classes_pdf_frame import mastro_CL_frame_settings
from .property_classes_album import mastro_CL_album_settings

classes = (
    mastro_CL_addon_properties,
    mastro_CL_constraint_XY_settings,
    mastro_CL_name_with_id,
    mastro_CL_street_name_list,
    mastro_CL_floor_name_list,
    mastro_CL_wall_name_list,
    mastro_CL_typology_uses_name_list,
    mastro_CL_use_name_list,
    mastro_CL_typology_name_list,
    mastro_CL_building_name_list,
    mastro_CL_block_name_list,
    mastro_CL_obj_typology_uses_name_list,
    mastro_CL_Sticky_Note,
    # mastro_CL_layer_slot must be registered before mastro_CL_layer_manager_props
    # because the latter uses it as a CollectionProperty type
    mastro_CL_layer_slot,
    mastro_CL_layer_manager_props,
    # mastro_CL_projector_batch_item must be registered before mastro_CL_projector_scene_props
    mastro_CL_projector_properties,
    mastro_CL_projector_batch_item,
    mastro_CL_camera_set_item,
    mastro_CL_camera_set,
    mastro_CL_projector_scene_props,
    mastro_CL_pdf_frame_item,
    mastro_CL_pdf_set,
    mastro_CL_pdf_scene_props,
    # mastro_CL_custom_property_string_name_list must be registered before
    # mastro_CL_custom_property_name_list because the latter uses it as CollectionProperty type
    mastro_CL_custom_property_string_name_list,
    mastro_CL_custom_property_name_list,
    mastro_CL_cad_pen,
    mastro_CL_cad_dash_pattern,
    mastro_CL_cad_layer,
    # mastro_CL_print_set_param must be registered before mastro_CL_print_set
    # because the latter uses it as a CollectionProperty type
    mastro_CL_print_set_param,
    mastro_CL_print_set,
    mastro_CL_print_scene_props,
    mastro_CL_frame_settings,
    mastro_CL_album_settings,
)