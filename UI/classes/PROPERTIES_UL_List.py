import bpy
from bpy.types import UIList

class PROPERTIES_UL_List(UIList):
    """Generic reusable UIList base class."""
    icon: str = 'DOT'
    list_name: str = ""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draws an item with an icon and ID."""
        if not self.list_name:
            return

        collection = getattr(context.scene, self.list_name)
        custom_icon = getattr(self, "icon", "DOT")

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.4)
            split.label(text=f"Id: {item.id}")
            split.prop(collection[index], "name", icon_only=True, icon=custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)

    def filter_items(self, context, data, propname):
        """Default: show all items."""
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        return filtered, []

    def draw_filter(self, context, layout):
        pass
    
# show the uses related to the selected typology    
class PROPERTIES_UL_Typology_Uses(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'COMMUNITY'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            id = item.id
            if item.name != "...":
                for el in context.scene.mastro_use_name_list:
                    if id == el.id:
                        # floorToFloor = round(el.floorToFloor,3)
                        storeys = el.storeys
                        liquid = el.liquid
                        break
                split = layout.split(factor=0.4)
                col1 = split.column()
                col2 = split.column()
                subSplit = col1.split(factor=0.4)
                subSplit1 = subSplit.column()
                subSplit2 = subSplit.column()
                if liquid:
                    subSplit1.label(text="Id: %d" % (item.id))
                    subSplit2.label(text="Storeys: variable")
                    # split.label(text="", icon = "MOD_LENGTH")
                else:
                    subSplit1.label(text="Id: %d" % (item.id))
                    subSplit2.label(text="Storeys: %s" % (storeys))
#             split.label(text=item.name, icon=custom_icon) 
                    
                col2.label(text=item.name)
            else:
                split = layout.split(factor=0.4)
                split.label(text="")
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
