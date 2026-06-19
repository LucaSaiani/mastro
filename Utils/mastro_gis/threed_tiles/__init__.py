import os
import tempfile

from .manager import BaseManager
from .blender import BlenderRenderer


GOOGLE_3DTILES_ROOT = "https://tile.googleapis.com/v1/3dtiles/root.json"


def download_tiles(bbox, lod, api_key, progress_cb=None, pivot=None, rotation_pivot=None, tile_root_name=None):
    """
    Download and import Google 3D Tiles for the given geographic bounding box.

    Parameters
    ----------
    bbox           : (xmin, ymin, xmax, ymax) in EPSG:3857 (Web Mercator metres)
    lod            : str, one of 'lod1' .. 'lod6'
    api_key        : str, Google Maps API key
    progress_cb    : callable(done, total) called after each tile import, or None
    pivot          : (lon, lat) in degrees used as the ECEF reference point for
                     placing imported geometry (translation only). Safe to let
                     this track wherever the user currently is (e.g. the live
                     scene origin) - it only affects how close to Blender's
                     (0,0,0) the content sits, not its orientation. Defaults
                     to this bbox's own center.
    rotation_pivot : (lon, lat) in degrees used to align local "up" with
                     Blender's Z axis. Unlike <pivot>, this MUST be the SAME
                     point across every call into a given scene (e.g. the
                     scene's original fixed geo origin, anchored once and
                     never recomputed) - Earth's curvature means the "up"
                     direction at two different points differs measurably
                     (~0.5 degrees over 50km), so batches downloaded with
                     different rotation pivots end up visibly tilted relative
                     to each other even though their positions are correct.
                     Defaults to <pivot> (only safe for a single download).
    tile_root_name : name of the empty (parented under the GIS Maps empty)
                     that this download's content is grouped under, e.g.
                     "3D Districts". Defaults to a generic name.
    """
    from ..proj import reprojPt

    # reproject bbox corners from EPSG:3857 to WGS84 (lon/lat degrees)
    min_lon, min_lat = reprojPt('EPSG:3857', 'EPSG:4326', bbox[0], bbox[1])
    max_lon, max_lat = reprojPt('EPSG:3857', 'EPSG:4326', bbox[2], bbox[3])

    if pivot is not None:
        center_lon, center_lat = pivot
    else:
        center_lon = (min_lon + max_lon) / 2.0
        center_lat = (min_lat + max_lat) / 2.0

    if rotation_pivot is not None:
        rotation_lon, rotation_lat = rotation_pivot
    else:
        rotation_lon, rotation_lat = center_lon, center_lat

    renderer = BlenderRenderer(
        threedTilesName=tile_root_name or "3D Tiles",
        join3dTilesObjects=False,
        instanceName="mastro",
        progress_cb=progress_cb,
    )

    manager = BaseManager(f"{GOOGLE_3DTILES_ROOT}?key={api_key}", renderer)
    manager.constantUriQuery = f"key={api_key}"
    manager.centerLat = center_lat
    manager.centerLon = center_lon
    manager.rotationLat = rotation_lat
    manager.rotationLon = rotation_lon
    manager.tilesDir = tempfile.mkdtemp(prefix="mastro_3dtiles_")
    manager.setGeometricError(BaseManager.geometricErrors[lod])
    manager.cacheJsonFiles = False
    manager.cache3dFiles = False

    result = manager.render(min_lon, min_lat, max_lon, max_lat)

    # clean up temp dir
    try:
        import shutil
        shutil.rmtree(manager.tilesDir, ignore_errors=True)
    except Exception:
        pass

    if isinstance(result, tuple) and len(result) == 1:
        # critical error returned as (error_message,)
        raise RuntimeError(result[0])

    num_tiles, errors = result
    return num_tiles, errors
