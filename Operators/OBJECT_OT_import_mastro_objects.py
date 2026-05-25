"""Import Mastro Objects from an external .blend file.

Flow:
  1. File → Import → Mastro Objects (.blend)   [file browser]
  2. Modal operator: status bar "Parsing file…" while loading
  3. invoke_props_dialog: tab Objects | Collection
       Objects   → scrollable UIList of mesh+GP, checkbox per item
       Collection→ pick one collection, imports everything inside
  4. Confirm → remap scene lists → link objects

Resolution order: Uses → Typologies → Walls → Floors → Streets → Buildings → Blocks
Matching: identical parameters → remap to existing; any difference → add as new entry.
"""

import bpy
import os
import re
import fnmatch as _fnmatch
from ..Utils.string_property_enum import register_string_enum

_custom_key_re = re.compile(r'^mastro_custom_(\d+)$')
from bpy.types import Operator, PropertyGroup, UIList, Menu
from bpy.props import (StringProperty, CollectionProperty,
                       EnumProperty, IntProperty, BoolProperty)


# ── PropertyGroups ────────────────────────────────────────────────────────────

class MASTRO_PG_ImportObject(PropertyGroup):
    selected:  BoolProperty(default=True)
    is_mastro: BoolProperty(default=False)
    obj_type:  StringProperty(default='MESH')   # 'MESH' | 'GP'


class MASTRO_PG_ImportCollection(PropertyGroup):
    pass   # name comes from PropertyGroup base



# ── Shared state ──────────────────────────────────────────────────────────────

_state: dict = {
    "all_obj_names":        [],
    "mastro_names":         set(),
    "obj_types":            {},   # {name: 'MESH'|'GP'}
    "all_collection_names": [],
    "collection_obj_map":   {},   # {coll_name: [obj_name, ...]}
    "filepath":             "",
    "remaps":               {},
    "select_op_ref":        None,
}


# ── Filter helper (shared by UIList and Toggle_All) ───────────────────────────

def _name_matches_filter(name, filter_text):
    if not filter_text:
        return True
    ft = filter_text.lower()
    n  = name.lower()
    if '*' in ft or '?' in ft or '[' in ft:
        return _fnmatch.fnmatch(n, ft)
    return ft in n


# ── UIList: scrollable object checklist ──────────────────────────────────────

class MASTRO_UL_ImportObjects(UIList):
    bl_idname = "MASTRO_UL_import_objects"

    use_filter_show: BoolProperty(default=True)

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        type_icon = ('OUTLINER_OB_GREASEPENCIL' if item.obj_type == 'GP'
                     else 'OUTLINER_OB_MESH')
        layout.prop(item, "selected", text="", emboss=False,
                    icon='CHECKBOX_HLT' if item.selected else 'CHECKBOX_DEHLT')
        layout.label(text="", icon=type_icon)
        layout.label(text="", icon='EVENT_M' if item.is_mastro else 'BLANK1')
        row = layout.row()
        row.alignment = 'LEFT'
        row.label(text=item.name)

    def draw_filter(self, context, layout):
        op = _state.get("select_op_ref")
        row = layout.row(align=True)
        row.prop(self, "filter_name",   text="", icon='VIEWZOOM')
        row.prop(self, "use_filter_invert", text="", icon='ARROW_LEFTRIGHT')
        if op is not None:
            row.separator()
            row.prop(op, "filter_mastro_only", text="", icon='EVENT_M',
                     toggle=True)

    def filter_items(self, context, data, propname):
        items       = getattr(data, propname)
        op          = _state.get("select_op_ref")
        mastro_only = op.filter_mastro_only if op else False
        # cache current filter state for Toggle_All
        _state["_filter_name"]   = self.filter_name
        _state["_filter_invert"] = self.use_filter_invert
        flags = []
        for item in items:
            match = _name_matches_filter(item.name, self.filter_name)
            if self.use_filter_invert and self.filter_name:
                match = not match
            if mastro_only and not item.is_mastro:
                match = False
            flags.append(self.bitflag_filter_item if match else 0)
        return flags, []


# ── UIList: collection picker ─────────────────────────────────────────────────

class MASTRO_UL_ImportCollections(UIList):
    bl_idname = "MASTRO_UL_import_collections"

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        layout.label(text=item.name, icon='OUTLINER_OB_GROUP_INSTANCE')

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        return [], []


# ── Specials menu ─────────────────────────────────────────────────────────────

class MASTRO_MT_ImportSpecials(Menu):
    bl_idname = "MASTRO_MT_import_specials"
    bl_label  = "Import Specials"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("object.mastro_import_toggle_all",
                             text="Select All", icon='CHECKBOX_HLT')
        op.select = True
        op = layout.operator("object.mastro_import_toggle_all",
                             text="Deselect All", icon='CHECKBOX_DEHLT')
        op.select = False


# ── Operator: toggle visible items ───────────────────────────────────────────

class OBJECT_OT_Import_Mastro_Toggle_All(Operator):
    bl_idname  = "object.mastro_import_toggle_all"
    bl_label   = "Toggle All"
    bl_options = {'INTERNAL'}

    select: BoolProperty()

    def execute(self, context):
        op = _state.get("select_op_ref")
        if op:
            ft          = _state.get("_filter_name",   "")
            inv         = _state.get("_filter_invert", False)
            mastro_only = getattr(op, "filter_mastro_only", False)
            for item in op.objects:
                match = _name_matches_filter(item.name, ft)
                if inv and ft:
                    match = not match
                if mastro_only and not item.is_mastro:
                    match = False
                if match:
                    item.selected = self.select
        return {'FINISHED'}


# ── Operator: selection dialog ────────────────────────────────────────────────

class OBJECT_OT_Import_Mastro_Select(Operator):
    """Choose what to import"""
    bl_idname  = "object.mastro_import_select"
    bl_label   = "Import Mastro Objects"
    bl_options = {'INTERNAL', 'UNDO'}

    mode: EnumProperty(
        items=[
            ('OBJECTS',    "Objects",    "Select individual objects"),
            ('COLLECTION', "Collection", "Import all objects from a collection"),
        ],
        default='OBJECTS',
    )
    objects:          CollectionProperty(type=MASTRO_PG_ImportObject)
    active_index:     IntProperty(default=0)
    collections:      CollectionProperty(type=MASTRO_PG_ImportCollection)
    collection_index: IntProperty(default=0)
    filter_mastro_only: BoolProperty(default=False)

    def invoke(self, context, event):
        _state["select_op_ref"] = self
        self.objects.clear()
        mastro_names = _state.get("mastro_names", set())
        obj_types    = _state.get("obj_types", {})
        for name in _state["all_obj_names"]:
            item           = self.objects.add()
            item.name      = name
            item.is_mastro = name in mastro_names
            item.selected  = True
            item.obj_type  = obj_types.get(name, 'MESH')
        self.collections.clear()
        for name in _state.get("all_collection_names", []):
            item      = self.collections.add()
            item.name = name
        return context.window_manager.invoke_props_dialog(self, width=480)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "mode", expand=True)
        layout.separator(factor=0.5)

        if self.mode == 'OBJECTS':
            n_sel = sum(1 for it in self.objects if it.selected)
            layout.label(text=f"{n_sel} / {len(self.objects)} selected")
            rows = min(20, max(5, len(self.objects)))
            row  = layout.row()
            row.template_list(
                "MASTRO_UL_import_objects", "",
                self, "objects",
                self, "active_index",
                rows=rows,
            )
            col = row.column(align=True)
            col.menu("MASTRO_MT_import_specials", icon='DOWNARROW_HLT', text="")

        else:
            if not self.collections:
                layout.label(text="No collections found in file.", icon='INFO')
            else:
                rows = min(20, max(5, len(self.collections)))
                layout.template_list(
                    "MASTRO_UL_import_collections", "",
                    self, "collections",
                    self, "collection_index",
                    rows=rows,
                )

    def execute(self, context):
        _state["select_op_ref"] = None
        if self.mode == 'OBJECTS':
            return self._execute_objects(context)
        return self._execute_collection(context)

    # ── Objects mode ──────────────────────────────────────────────────────────

    def _execute_objects(self, context):
        selected_names = [it.name for it in self.objects if it.selected]
        if not selected_names:
            self._discard_all()
            self.report({'WARNING'}, "Nothing selected.")
            return {'CANCELLED'}
        for it in self.objects:
            if not it.selected:
                obj = bpy.data.objects.get(it.name)
                if obj:
                    bpy.data.objects.remove(obj, do_unlink=True)
        return self._remap_and_finish(context, selected_names)

    # ── Collection mode ───────────────────────────────────────────────────────

    def _execute_collection(self, context):
        if not self.collections:
            self._discard_all()
            self.report({'WARNING'}, "No collection to import.")
            return {'CANCELLED'}
        coll_name      = self.collections[self.collection_index].name
        selected_names = _state.get("collection_obj_map", {}).get(coll_name, [])
        if not selected_names:
            self._discard_all()
            self.report({'WARNING'}, "Selected collection is empty.")
            return {'CANCELLED'}
        sel_set = set(selected_names)
        for name in _state["all_obj_names"]:
            if name not in sel_set:
                obj = bpy.data.objects.get(name)
                if obj:
                    bpy.data.objects.remove(obj, do_unlink=True)
        return self._remap_and_finish(context, selected_names)

    # ── Shared remap + hand-off ───────────────────────────────────────────────

    def _remap_and_finish(self, context, selected_names):
        mastro_names = _state.get("mastro_names", set())
        mastro_objs  = [bpy.data.objects.get(n) for n in selected_names
                        if n in mastro_names and bpy.data.objects.get(n)]

        # Load scene now (deferred from initial load) for remap data.
        src_scene = None
        fp = _state.get("filepath", "")
        if fp:
            try:
                # Record existing objects before loading to clean up afterwards.
                existing_obj_names = set(bpy.data.objects.keys())
                with bpy.data.libraries.load(fp, link=False) as (src, dst):
                    dst.scenes = src.scenes[:1]
                src_scene = dst.scenes[0] if dst.scenes else None
                # Remove any objects the scene load pulled in as copies.
                for name in set(bpy.data.objects.keys()) - existing_obj_names:
                    obj = bpy.data.objects.get(name)
                    if obj:
                        bpy.data.objects.remove(obj, do_unlink=True)
            except Exception as e:
                self.report({'WARNING'}, f"Could not load scene for remap: {e}")
        else:
            self.report({'WARNING'}, "Filepath missing — scene attributes will not be remapped.")

        if src_scene is None and mastro_objs:
            self.report({'WARNING'}, "Source scene not found — scene list entries will not be imported.")

        scene  = context.scene
        unique = _collect_unique_entries(mastro_objs, src_scene)

        use_remap   = _build_remap(unique["use"],      "use",      scene)
        for tid in unique["typology"]:
            unique["typology"][tid]["useList"] = _remap_use_list(
                unique["typology"][tid]["useList"], use_remap)
        typo_remap  = _build_remap(unique["typology"], "typology", scene)
        wall_remap  = _build_remap(unique["wall"],     "wall",     scene)
        floor_remap = _build_remap(unique["floor"],    "floor",    scene)
        str_remap   = _build_remap(unique["street"],   "street",   scene)
        bld_remap    = _build_remap(unique["building"], "building", scene)
        blk_remap    = _build_remap(unique["block"],    "block",    scene)
        custom_remap, string_opt_remaps = _ensure_custom_props(unique["custom"], scene)

        if src_scene:
            bpy.data.scenes.remove(src_scene, do_unlink=True)

        remaps = {
            "use": use_remap, "typology": typo_remap, "wall": wall_remap,
            "floor": floor_remap, "street": str_remap,
            "building": bld_remap, "block": blk_remap,
            "custom": custom_remap, "string_opts": string_opt_remaps,
        }

        imported = []
        for name in selected_names:
            obj = bpy.data.objects.get(name)
            if obj is None:
                continue
            if name not in scene.collection.objects:
                scene.collection.objects.link(obj)
            imported.append(obj)

        _apply_remap_to_objects(mastro_objs, remaps)

        if imported:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in imported:
                obj.select_set(True)
            context.view_layer.objects.active = imported[0]

        _state.clear()
        self.report({'INFO'}, f"Imported {len(imported)} object(s): {', '.join(o.name for o in imported)}.")
        return {'FINISHED'}

    def _discard_all(self):
        for name in _state.get("all_obj_names", []):
            obj = bpy.data.objects.get(name)
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)
        _state.update({"all_obj_names": [], "mastro_names": set(),
                        "obj_types": {}, "all_collection_names": [],
                        "collection_obj_map": {}, "filepath": "",
                        "remaps": {}})


# ── Operator: file browser + modal loading phase ─────────────────────────────

class OBJECT_OT_Import_Mastro_Objects(Operator):
    """Import Mastro objects from a .blend file"""
    bl_idname  = "object.mastro_import_objects"
    bl_label   = "Mastro Objects (.blend)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath:    StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.blend", options={'HIDDEN'})

    _timer = None
    _ticks = 0

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        fp = bpy.path.abspath(self.filepath)
        if not os.path.isfile(fp):
            self.report({'ERROR'}, f"File not found: {fp}")
            return {'CANCELLED'}

        _state.update({"all_obj_names": [], "mastro_names": set(),
                        "obj_types": {}, "all_collection_names": [],
                        "collection_obj_map": {}, "filepath": "",
                        "remaps": {}, "select_op_ref": None,
                        "_filepath": fp})
        self._ticks = 0
        self._timer = context.window_manager.event_timer_add(0.05, window=context.window)
        context.window_manager.modal_handler_add(self)
        context.workspace.status_text_set("Mastro Import: reading file…")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        self._ticks += 1
        if self._ticks < 2:
            return {'RUNNING_MODAL'}

        context.window_manager.event_timer_remove(self._timer)
        self._timer = None
        context.workspace.status_text_set(None)

        fp     = _state.pop("_filepath", "")
        result = self._load_file(context, fp)
        if result == 'CANCELLED':
            return {'CANCELLED'}

        bpy.ops.object.mastro_import_select('INVOKE_DEFAULT')
        return {'FINISHED'}

    def _load_file(self, context, fp):
        try:
            with bpy.data.libraries.load(fp, link=False) as (src, dst):
                src_coll_names  = list(src.collections)
                dst.objects     = list(src.objects)
                dst.collections = list(src.collections)
        except Exception as e:
            self.report({'ERROR'}, f"Could not read file: {e}")
            return 'CANCELLED'

        all_objects = [o for o in dst.objects if o is not None]

        mesh_gp = [o for o in all_objects if _is_mesh_or_gp(o)]
        for o in all_objects:
            if not _is_mesh_or_gp(o):
                bpy.data.objects.remove(o, do_unlink=True)

        if not mesh_gp:
            self.report({'WARNING'}, "No mesh or grease pencil objects found.")
            return 'CANCELLED'

        mesh_gp_names = {o.name for o in mesh_gp}
        mastro_names  = {o.name for o in mesh_gp if _is_mastro_object(o)}
        obj_types     = {o.name: ('GP' if _is_gp_object(o) else 'MESH') for o in mesh_gp}

        collection_obj_map = {}
        for orig_name, coll in zip(src_coll_names, dst.collections):
            if coll is None:
                continue
            names = [o.name for o in coll.all_objects
                     if _is_mesh_or_gp(o) and o.name in mesh_gp_names]
            if names:
                collection_obj_map[orig_name] = names

        _state["filepath"]             = fp
        _state["all_obj_names"]        = sorted(mesh_gp_names)
        _state["mastro_names"]         = mastro_names
        _state["obj_types"]            = obj_types
        _state["all_collection_names"] = sorted(collection_obj_map.keys())
        _state["collection_obj_map"]   = collection_obj_map
        return 'FINISHED'


# ── Object type helpers ───────────────────────────────────────────────────────

def _is_gp_object(obj):
    return obj.type in ('GPENCIL', 'GREASE_PENCIL')


def _is_mesh_or_gp(obj):
    return obj.type == 'MESH' or _is_gp_object(obj)


def _is_mastro_object(obj):
    if not _is_mesh_or_gp(obj):
        return False
    m = obj.data
    return bool(m.get("MaStro object") or m.get("MaStro mass")
                or m.get("MaStro block") or m.get("MaStro street"))


# ── Domain utilities ──────────────────────────────────────────────────────────

def _attr_values(obj, attr_name, domain):
    mesh = obj.data
    if attr_name not in mesh.attributes:
        return set()
    attr = mesh.attributes[attr_name]
    if attr.domain != domain:
        return set()
    return {d.value for d in attr.data}


def _by_id(collection, eid):
    return next((e for e in collection if e.id == eid), None)


def _collect_unique_entries(objects, src_scene):
    unique = {t: {} for t in
              ("use","typology","wall","floor","street","building","block","custom")}
    if not objects or src_scene is None:
        return unique
    for obj in objects:
        mesh      = obj.data
        is_block  = bool(mesh.get("MaStro block"))
        is_street = bool(mesh.get("MaStro street"))

        for attr in (["mastro_typology_id"] +
                     (["mastro_typology_id_EDGE"] if is_block else [])):
            dom = "EDGE" if attr.endswith("_EDGE") else "FACE"
            for tid in _attr_values(obj, attr, dom):
                if tid in unique["typology"]:
                    continue
                e = _by_id(src_scene.mastro_typology_name_list, tid)
                if e:
                    unique["typology"][tid] = {
                        "name": e.name, "useList": e.useList,
                        "typologyEdgeColor": tuple(e.typologyEdgeColor)}

        for wid in _attr_values(obj, "mastro_wall_id", "EDGE"):
            if wid in unique["wall"]:
                continue
            e = _by_id(src_scene.mastro_wall_name_list, wid)
            if e:
                unique["wall"][wid] = {
                    "name": e.name, "wallThickness": e.wallThickness,
                    "wallOffset": e.wallOffset, "normal": e.normal,
                    "wallEdgeColor": tuple(e.wallEdgeColor)}

        for attr, dom in [("mastro_floor_id","FACE"),("mastro_floor_id_EDGE","EDGE")]:
            for fid in _attr_values(obj, attr, dom):
                if fid in unique["floor"]:
                    continue
                e = _by_id(src_scene.mastro_floor_name_list, fid)
                if e:
                    unique["floor"][fid] = {"name": e.name}

        if is_street:
            for sid in _attr_values(obj, "mastro_street_id", "EDGE"):
                if sid in unique["street"]:
                    continue
                e = _by_id(src_scene.mastro_street_name_list, sid)
                if e:
                    unique["street"][sid] = {
                        "name": e.name, "streetWidth": e.streetWidth,
                        "streetRadius": e.streetRadius,
                        "streetEdgeColor": tuple(e.streetEdgeColor)}

        bid = obj.mastro_props.mastro_building_attribute
        if bid is not None and bid not in unique["building"]:
            e = _by_id(src_scene.mastro_building_name_list, bid)
            if e:
                unique["building"][bid] = {"name": e.name}

        blk = obj.mastro_props.mastro_block_attribute
        if blk is not None and blk not in unique["block"]:
            e = _by_id(src_scene.mastro_block_name_list, blk)
            if e:
                unique["block"][blk] = {"name": e.name}

        for prop in src_scene.mastro_custom_property_name_list:
            if not prop.committed or f"_{prop.name}" not in obj:
                continue
            if prop.name not in unique["custom"]:
                unique["custom"][prop.name] = {
                    "name": prop.name,
                    "property_type": prop.property_type,
                    "string_options": [(o.id, o.name) for o in prop.string_options],
                }

    for _tid, tp in unique["typology"].items():
        for uid_str in tp["useList"].split(";"):
            uid_str = uid_str.strip()
            if not uid_str:
                continue
            uid = int(uid_str)
            if uid in unique["use"]:
                continue
            e = _by_id(src_scene.mastro_use_name_list, uid)
            if e:
                unique["use"][uid] = {
                    "name": e.name, "floorToFloor": e.floorToFloor,
                    "storeys": e.storeys, "liquid": e.liquid}
    return unique


def _params_match(a, b):
    for k, va in a.items():
        if k not in b:
            return False
        vb = b[k]
        if isinstance(va, float):
            if abs(va - vb) > 1e-5:
                return False
        elif isinstance(va, tuple):
            if any(abs(x - y) > 1e-5 for x, y in zip(va, vb)):
                return False
        elif va != vb:
            return False
    return True



def _scene_params(entry, list_type):
    if list_type == "use":
        return {"name": entry.name, "floorToFloor": entry.floorToFloor,
                "storeys": entry.storeys, "liquid": entry.liquid}
    if list_type == "typology":
        return {"name": entry.name, "useList": entry.useList,
                "typologyEdgeColor": tuple(entry.typologyEdgeColor)}
    if list_type == "wall":
        return {"name": entry.name, "wallThickness": entry.wallThickness,
                "wallOffset": entry.wallOffset, "normal": entry.normal,
                "wallEdgeColor": tuple(entry.wallEdgeColor)}
    if list_type == "floor":
        return {"name": entry.name}
    if list_type == "street":
        return {"name": entry.name, "streetWidth": entry.streetWidth,
                "streetRadius": entry.streetRadius,
                "streetEdgeColor": tuple(entry.streetEdgeColor)}
    if list_type in ("building", "block"):
        return {"name": entry.name}
    if list_type == "custom":
        return {"name": entry.name, "property_type": entry.property_type}
    return {}


def _get_scene_list(scene, list_type):
    return {"use": scene.mastro_use_name_list,
            "typology": scene.mastro_typology_name_list,
            "wall": scene.mastro_wall_name_list,
            "floor": scene.mastro_floor_name_list,
            "street": scene.mastro_street_name_list,
            "building": scene.mastro_building_name_list,
            "block":   scene.mastro_block_name_list,
            "custom":  scene.mastro_custom_property_name_list}[list_type]


def _next_free_id(collection):
    used = {e.id for e in collection}
    i = 1
    while i in used:
        i += 1
    return i


def _add_entry(collection, list_type, params, new_id):
    item = collection.add(); item.id = new_id; item.name = params["name"]
    if list_type == "use":
        item.floorToFloor = params["floorToFloor"]
        item.storeys = params["storeys"]; item.liquid = params["liquid"]
    elif list_type == "typology":
        item.useList = params["useList"]
        item.typologyEdgeColor = params["typologyEdgeColor"]
    elif list_type == "wall":
        item.wallThickness = params["wallThickness"]
        item.wallOffset = params["wallOffset"]; item.normal = params["normal"]
        item.wallEdgeColor = params["wallEdgeColor"]
    elif list_type == "street":
        item.streetWidth = params["streetWidth"]
        item.streetRadius = params["streetRadius"]
        item.streetEdgeColor = params["streetEdgeColor"]
    elif list_type == "custom":
        item.property_type = params["property_type"]
        item.committed = True
        item.previous_name = item.name


def _next_free_string_opt_id(string_options):
    used = {o.id for o in string_options}
    i = 1
    while i in used:
        i += 1
    return i


def _ensure_custom_props(unique_custom, scene):
    """Ensure all imported custom properties exist in dst scene.
    Returns (set of names, {prop_name: {src_opt_id: dst_opt_id}})."""
    collection = scene.mastro_custom_property_name_list
    string_id_remaps = {}  # {prop_name: {src_id: dst_id}}

    for prop_name, params in unique_custom.items():
        existing = next((e for e in collection if e.name == prop_name), None)
        if existing is None:
            new_id = _next_free_id(collection)
            item = collection.add()
            item.id = new_id
            item.name = params["name"]
            item.previous_name = params["name"]
            item.property_type = params["property_type"]
            item.committed = True
            remap = {}
            for src_id, opt_name in params.get("string_options", []):
                opt = item.string_options.add()
                opt.id = _next_free_string_opt_id(item.string_options)
                opt.name = opt_name
                remap[src_id] = opt.id
            if params["property_type"] == 'STRING':
                register_string_enum(item.id)
        else:
            item = existing
            remap = {}
            for src_id, opt_name in params.get("string_options", []):
                dst = next((o for o in item.string_options if o.name == opt_name), None)
                if dst is None:
                    opt = item.string_options.add()
                    opt.id = _next_free_string_opt_id(item.string_options)
                    opt.name = opt_name
                    remap[src_id] = opt.id
                else:
                    remap[src_id] = dst.id
        string_id_remaps[prop_name] = remap

    return set(unique_custom.keys()), string_id_remaps


def _remap_use_list(use_list_str, use_remap):
    parts = [p.strip() for p in use_list_str.split(";") if p.strip()]
    return ";".join(str(use_remap.get(int(p), int(p))) for p in parts)


def _build_remap(unique_entries, list_type, scene, use_remap=None):
    remap = {}; collection = _get_scene_list(scene, list_type)
    for src_id, params in unique_entries.items():
        cmp = dict(params)
        if list_type == "typology" and use_remap:
            cmp["useList"] = _remap_use_list(params["useList"], use_remap)
        match_id = next((e.id for e in collection
                         if _params_match(cmp, _scene_params(e, list_type))), None)
        if match_id is not None:
            remap[src_id] = match_id
        else:
            new_id = _next_free_id(collection)
            _add_entry(collection, list_type, cmp, new_id)
            remap[src_id] = new_id
    return remap


def _apply_remap_to_objects(objects, remaps):
    def _remap_attr(obj, attr_name, domain, id_map):
        mesh = obj.data
        if attr_name not in mesh.attributes:
            return
        attr = mesh.attributes[attr_name]
        if attr.domain != domain:
            return
        for item in attr.data:
            v = id_map.get(item.value)
            if v is not None:
                item.value = v
        mesh.update()

    for obj in objects:
        mesh      = obj.data
        is_block  = bool(mesh.get("MaStro block"))
        is_street = bool(mesh.get("MaStro street"))
        if "typology" in remaps:
            _remap_attr(obj, "mastro_typology_id", "FACE", remaps["typology"])
            if is_block:
                _remap_attr(obj, "mastro_typology_id_EDGE", "EDGE", remaps["typology"])
        if "wall"  in remaps:
            _remap_attr(obj, "mastro_wall_id", "EDGE", remaps["wall"])
        if "floor" in remaps:
            _remap_attr(obj, "mastro_floor_id", "FACE", remaps["floor"])
            if is_block:
                _remap_attr(obj, "mastro_floor_id_EDGE", "EDGE", remaps["floor"])
        if "street" in remaps and is_street:
            _remap_attr(obj, "mastro_street_id", "EDGE", remaps["street"])
        if "building" in remaps:
            old = obj.mastro_props.mastro_building_attribute
            new = remaps["building"].get(old)
            if new is not None:
                obj.mastro_props.mastro_building_attribute = new
        if "block" in remaps:
            old = obj.mastro_props.mastro_block_attribute
            new = remaps["block"].get(old)
            if new is not None:
                obj.mastro_props.mastro_block_attribute = new
        # remap string option ids on STRING custom properties
        if "string_opts" in remaps:
            for prop_name, opt_remap in remaps["string_opts"].items():
                key = f"_{prop_name}"
                if key in obj and opt_remap:
                    old_val = obj[key]
                    new_val = opt_remap.get(old_val)
                    if new_val is not None:
                        obj[key] = new_val
