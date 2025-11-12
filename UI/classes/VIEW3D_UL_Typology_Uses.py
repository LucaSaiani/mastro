import bpy 
from bpy.types import UIList

"""UI List object used in the view 3D mass panel to show
the assigned uses of the selected face"""
class VIEW3D_UL_Typology_Uses(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'COMMUNITY'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.5)
            split.label(text="Storeys: %s" % (item.storeys))
            split.label(text=item.name)
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass