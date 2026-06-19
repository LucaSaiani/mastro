from os.path import basename, join as joinStrings, exists as pathExists
from os import remove as removeFile
from math import radians, atan, sqrt, pi
import re
from operator import itemgetter
import sys

import bpy
from mathutils import Vector, Matrix

from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter

from ..geoscene import GIS_MAPS_NAME


def _create_collection(name):
    """Get or create a Blender collection linked to the scene (used only as
    a temporary staging area for the glTF importer, see collection_import)."""
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _get_or_create_named_empty(scn, name, parent=None):
    """Get or create a PLAIN_AXES empty linked to the scene's root
    collection, optionally parented (e.g. under the GIS Maps empty used by
    the regular 2D basemap tiles, so 3D Tiles content lives in the same
    hierarchy instead of a separate dedicated collection)."""
    obj = scn.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.empty_display_size = 0.0
        scn.collection.objects.link(obj)
        if parent is not None:
            obj.parent = parent
        if name == GIS_MAPS_NAME:
            # store the geo-origin at creation time, mirroring the 2D
            # basemap's _get_or_create_empty - moveOriginPrj() needs this to
            # compute GIS Maps' absolute Blender position later. If 3D Tiles
            # happens to be the first GIS content ever created in a scene,
            # this empty would otherwise be missing these properties forever
            # (only ever set "on first creation" by either code path), which
            # silently breaks the whole pan/origin-shift compensation system.
            from ..geoscene import GeoScene
            gs = GeoScene(scn)
            obj['initial_crsx'] = gs.crsx if gs.hasOriginPrj else 0.0
            obj['initial_crsy'] = gs.crsy if gs.hasOriginPrj else 0.0
    return obj


def find_layer_collection(layer_col: bpy.types.LayerCollection, target_col: bpy.types.Collection):
    """
    Recursively searches for the LayerCollection that corresponds to the given <target_col> of type <bpy.types.Collection>
    within the hierarchy starting from <layer_col> of type <bpy.types.LayerCollection>
    Returns the found LayerCollection or None if not found.
    """
    if layer_col.collection == target_col:
        return layer_col
    for child in layer_col.children:
        found = find_layer_collection(child, target_col)
        if found:
            return found
    return None


class BlenderRenderer:

    def __init__(self, threedTilesName, join3dTilesObjects, instanceName, progress_cb=None):
        self.threedTilesName = threedTilesName
        self.join3dTilesObjects = join3dTilesObjects
        self.instanceName = instanceName
        self.progress_cb = progress_cb  # callable(done, total) or None

        self.calculateHeightOffset = False
        self.heightOffset = 0.

        self.licenseRePattern = re.compile(rb'"copyright":\s*"(\w+)"')
        self.copyrightHolders = {}

        self._gltfImporterPatched = None
        self._set_convert_functions = None
        self._select_imported_objects = None

    def prepare(self, manager):
        self.num_imported_tiles = 0

        # 3D Tiles content lives under the same "GIS Maps" empty hierarchy as
        # the regular 2D basemap tiles, grouped per quality level (so
        # repeated downloads at different LODs don't mix), instead of a
        # separate dedicated collection.
        scn = bpy.context.scene
        gis_maps = _get_or_create_named_empty(scn, GIS_MAPS_NAME)
        self.tile_root = _get_or_create_named_empty(scn, self.threedTilesName, parent=gis_maps)
        # Objects accumulate under tile_root across repeated downloads into
        # the same scene. finalize() re-aligns/re-orients geometry using
        # THIS call's center - it must only touch objects imported in this
        # call, otherwise it re-rotates already-correctly-placed older
        # objects using the wrong (new) alignment, visibly tilting them.
        self._new_objects = []

        self.collection_import = _create_collection(self.threedTilesName + "_import")
        self.layer_collection_import = find_layer_collection(
            bpy.context.view_layer.layer_collection,
            self.collection_import
        )
        bpy.context.view_layer.active_layer_collection = self.layer_collection_import

        self.centerCoords = manager.fromGeographic(manager.centerLat, manager.centerLon, 0.)
        # The ENU "up" alignment rotation (see finalize()) must stay anchored
        # to ONE fixed point for the scene's whole lifetime, not the current
        # call's (possibly panned-to) center - otherwise batches downloaded
        # from different locations end up tilted relative to each other by
        # the angle Earth's curvature introduces between those two points.
        rotation_lat = getattr(manager, 'rotationLat', None)
        rotation_lon = getattr(manager, 'rotationLon', None)
        if rotation_lat is None or rotation_lon is None:
            rotation_lat, rotation_lon = manager.centerLat, manager.centerLon
        self.rotationLon = rotation_lon
        self.rotationCoords = manager.fromGeographic(rotation_lat, rotation_lon, 0.)

        glTFImporter._patch_convert_functions = True
        self.patchGltfImporter()

    def finalize(self, manager):
        bpy.data.collections.remove(self.collection_import)
        self.collection_import = None
        self.layer_collection_import = None

        new_objects = self._new_objects

        if not new_objects:
            if not self.tile_root.children:
                bpy.data.objects.remove(self.tile_root)
            self.tile_root = None

            if self._gltfImporterPatched:
                self.cleanupGltfImporterPatching()
            return

        bpy.ops.object.select_all(action='DESELECT')

        if sum(1 for obj in new_objects if obj.parent):
            mesh_objects = {obj.name: obj for obj in new_objects if obj.type == 'MESH'}
            while True:
                num_processed_objects = 0
                for obj in list(mesh_objects.values()):
                    if obj.parent and not obj.children:
                        mw = obj.matrix_world.copy()
                        obj.parent = None
                        obj.matrix_world = mw
                        del mesh_objects[obj.name]
                        num_processed_objects += 1
                if num_processed_objects == 0 or not mesh_objects:
                    break
            for obj in [obj for obj in new_objects if obj.type == 'EMPTY']:
                new_objects.remove(obj)
                bpy.data.objects.remove(obj)

        for obj in new_objects:
            obj.select_set(True)

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        centerCoords = self.centerCoords
        rotationCoords = self.rotationCoords
        lat = atan(rotationCoords[2]/sqrt(rotationCoords[0]*rotationCoords[0] + rotationCoords[1]*rotationCoords[1]))
        matrix = Matrix.Rotation(lat-pi/2., 4, 'X') @ Matrix.Rotation(radians(-90. - self.rotationLon), 4, 'Z')

        locationsAfterRotation = [(matrix @ obj.location) for obj in new_objects]

        heightOffset = min(location[2] for location in locationsAfterRotation)\
            if self.calculateHeightOffset else\
            self.heightOffset
        if self.calculateHeightOffset:
            self.heightOffset = heightOffset

        if self.join3dTilesObjects:
            self.joinObjects(new_objects)

            _cursorLocation = bpy.context.scene.cursor.location.copy()
            bpy.context.scene.cursor.location = (0., 0., 0.) if self._gltfImporterPatched else centerCoords
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            bpy.context.scene.cursor.location = _cursorLocation

            new_objects[0].matrix_local = matrix
            new_objects = [new_objects[0]]
        else:
            if not self._gltfImporterPatched:
                centerCoords = matrix @ centerCoords
            for obj, location in zip(new_objects, locationsAfterRotation):
                if not self._gltfImporterPatched:
                    location[2] -= centerCoords[2]
                obj.matrix_local = Matrix.Translation(location) @ matrix
                obj.select_set(True)

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        bpy.ops.object.select_all(action='DESELECT')

        # Group this download's content under the LOD-named empty (already
        # parented to GIS Maps). Deliberately NOT preserving "current world
        # position" here (unlike _reparent_keep_world): the position/rotation
        # just computed above is already anchor-relative (both pivots are
        # fixed to GIS Maps' original anchor, see the operator), i.e. exactly
        # the kind of time-invariant LOCAL offset _parent_tile() also uses
        # for regular 2D tiles. Treating it as a literal "world position
        # snapshot" instead would double-count GIS Maps' current pan-
        # compensating shift, landing overlapping re-downloads (after
        # panning) at the wrong spot relative to earlier ones.
        for obj in new_objects:
            obj.parent = self.tile_root

        # store copyright as a scene custom property instead of blosm-specific attribute
        if self.copyrightHolders:
            bpy.context.scene["3dtiles_copyright"] = "; ".join(
                entry[0] for entry in reversed(
                    sorted(self.copyrightHolders.items(), key=itemgetter(1))
                )
            )

        if self._gltfImporterPatched:
            self.cleanupGltfImporterPatching()

        self.tile_root = None

    def renderGlb(self, manager, uri, path, transformMatrix, cacheContent):
        context = bpy.context

        filepath = joinStrings(
            manager.tilesDir,
            basename(path) if cacheContent else ("current_file_" + self.instanceName + ".glb" if self.instanceName else "current_file.glb")
        )

        if cacheContent:
            if not pathExists(filepath):
                fileContent = manager.download(uri)
                with open(filepath, 'wb') as f:
                    f.write(fileContent)
            bpy.ops.import_scene.gltf(filepath=filepath, import_scene_as_collection=True)
        else:
            fileContent = manager.download(uri)

            match = re.search(self.licenseRePattern, fileContent)
            if match:
                self.processCopyrightInfo(match.group(1).decode('utf-8'))

            with open(filepath, 'wb') as f:
                f.write(fileContent)

            bpy.ops.import_scene.gltf(filepath=filepath, import_scene_as_collection=True)

            if self.collection_import.objects:
                self.finalize_glb_import(filepath, transformMatrix)

    def renderB3dm(self, manager, uri, path, transformMatrix, cacheContent):
        import numpy
        from .py3dtiles.tileset.content.tile_content_reader import read_array

        filepath = joinStrings(
            manager.tilesDir,
            basename(path)[:-4] + "glb" if cacheContent else ("current_file_" + self.instanceName + ".glb" if self.instanceName else "current_file.glb")
        )

        if cacheContent:
            if not pathExists(filepath):
                fileContent = manager.download(uri)
                with open(filepath, 'wb') as f:
                    f.write(fileContent)
            bpy.ops.import_scene.gltf(filepath=filepath, import_scene_as_collection=True)
        else:
            fileContent = manager.download(uri)
            match = re.search(self.licenseRePattern, fileContent)
            if match:
                self.processCopyrightInfo(match.group(1).decode('utf-8'))

            b3dmContent = read_array( numpy.frombuffer(fileContent, dtype=numpy.uint8) )
            if b3dmContent is None or b3dmContent.header is None:
                raise Exception("The file doesn't contain a valid data.")

            gltfContent = b3dmContent.body.gltf
            rtc_center = b3dmContent.body.feature_table.header.data.get("RTC_CENTER")
            if rtc_center:
                from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter
                _patch_convert_functions = glTFImporter._patch_convert_functions
                glTFImporter._patch_convert_functions = False

            with open(filepath, 'wb') as f:
                f.write(gltfContent.to_array())

            try:
                bpy.ops.import_scene.gltf(filepath=filepath, import_scene_as_collection=True)
            finally:
                if rtc_center:
                    glTFImporter._patch_convert_functions = _patch_convert_functions

            if self.collection_import.objects or self.collection_import.children:
                if rtc_center:
                    self.process_rtc(rtc_center)
                self.finalize_glb_import(filepath, transformMatrix)

    def processCopyrightInfo(self, info):
        for copyrightHolder in info.split(';'):
            copyrightHolder = copyrightHolder.strip()
            if not copyrightHolder in self.copyrightHolders:
                self.copyrightHolders[copyrightHolder] = 0
            self.copyrightHolders[copyrightHolder] += 1

    def process_rtc(self, rtc_center):
        rtc_center = Vector(rtc_center)

        collection = self.collection_import
        if self.collection_import.children:
            collection = next((c for c in self.layer_collection_import.children if not c.exclude)).collection

        for obj in collection.objects:
            if not obj.parent:
                obj.matrix_world = Matrix.Translation(rtc_center - self.centerCoords) @ obj.matrix_world

    def finalize_glb_import(self, filepath, transformMatrix):
        removeFile(filepath)

        collection = self.collection_import
        if self.collection_import.children:
            collection = next((c for c in self.layer_collection_import.children if not c.exclude)).collection

        scn = bpy.context.scene
        for obj in collection.objects:
            collection.objects.unlink(obj)
            scn.collection.objects.link(obj)
            self._new_objects.append(obj)
            if transformMatrix:
                self.apply_transform_matrix(obj, transformMatrix)

        if self.collection_import.children:
            for collection in self.collection_import.children:
                bpy.data.collections.remove(collection)

        self.num_imported_tiles += 1
        if self.progress_cb:
            self.progress_cb(self.num_imported_tiles, 0)  # total unknown until traversal ends

    def apply_transform_matrix(self, obj, transformMatrix):
        u = 1.0 / bpy.context.scene.unit_settings.scale_length

        center = u * self.centerCoords
        m = transformMatrix.copy()
        m.translation *= u

        obj.matrix_world = Matrix.Translation(-center) @ m @ Matrix.Translation(center) @ obj.matrix_world


    def joinObjects(self, objects):
        bpy.context.view_layer.objects.active = objects[0]

        if len(objects) > 1:
            bpy.ops.object.join()

        joinedObject = objects[0]
        joinedObject.name = self.threedTilesName

    def patchGltfImporter(self):
        bv = bpy.app.version

        if (bv[0] == 3 and bv[1] == 6) or (bv[0] == 4 and bv[1] <= 2):
            from .gltf_patch import set_convert_functions_4_5, select_imported_objects_4_1
            from io_scene_gltf2.blender.imp.gltf2_blender_gltf import BlenderGlTF
            from io_scene_gltf2.blender.imp.gltf2_blender_scene import BlenderScene

            glTFImporter._offset = self.centerCoords

            self._set_convert_functions = BlenderGlTF.set_convert_functions
            BlenderGlTF.set_convert_functions = set_convert_functions_4_5

            self._select_imported_objects = BlenderScene.select_imported_objects
            BlenderScene.select_imported_objects = select_imported_objects_4_1

            self._gltfImporterPatched = (glTFImporter, BlenderGlTF, BlenderScene)
        elif (bv[0] == 4 and 3 <= bv[1]) or bv[0] > 4:
            from .gltf_patch import set_convert_functions_4_5, select_imported_objects_4_1
            from io_scene_gltf2.blender.imp.blender_gltf import BlenderGlTF
            from io_scene_gltf2.blender.imp.scene import BlenderScene

            glTFImporter._offset = self.centerCoords

            self._set_convert_functions = BlenderGlTF.set_convert_functions
            BlenderGlTF.set_convert_functions = set_convert_functions_4_5

            self._select_imported_objects = BlenderScene.select_imported_objects
            BlenderScene.select_imported_objects = select_imported_objects_4_1

            self._gltfImporterPatched = (glTFImporter, BlenderGlTF, BlenderScene)

    def cleanupGltfImporterPatching(self):
        glTFImporter, BlenderGlTF, BlenderScene = self._gltfImporterPatched

        BlenderGlTF.set_convert_functions = self._set_convert_functions
        self._set_convert_functions = None

        delattr(glTFImporter, "_patch_convert_functions")
        delattr(glTFImporter, "_offset")

        BlenderScene.select_imported_objects = self._select_imported_objects
        self._select_imported_objects = None

        self._gltfImporterPatched = None
