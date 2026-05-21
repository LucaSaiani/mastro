"""
Quick shadow render test script.
Paste into Blender's Text Editor and run with Alt+R.

Renders a single Workbench frame and saves to /tmp/shadow_test.png.
Set USE_REAL_LIGHT=True to use the active camera's assigned light source
instead of a virtual az/el direction.
"""

import bpy
import math
import numpy as np
import os
from mathutils import Vector

scene  = bpy.context.scene
camera = scene.camera
render = scene.render

# ── PARAMETERS ────────────────────────────────────────────────────────────────

USE_REAL_LIGHT = True   # True = use the light object assigned to the camera
                        # False = use virtual AZIMUTH/ELEVATION below

AZIMUTH_DEG   = 45.0
ELEVATION_DEG = 45.0

LIGHT_MODE       = 'FLAT'
FILM_TRANSPARENT = True
SHOW_SHADOWS     = True
EXPOSURE         = 2.0
OUT_PATH         = "/tmp/shadow_test.png"

# ── Compute light direction ───────────────────────────────────────────────────

if USE_REAL_LIGHT:
    cam_cl = camera.data.mastro_projector_cl
    light  = cam_cl.light_source
    if light and light.type == 'LIGHT':
        light_dir = (light.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
        print(f"Using real light: {light.name}  light_dir={tuple(round(v,4) for v in light_dir)}")
    else:
        print("No real light assigned — falling back to virtual az/el")
        USE_REAL_LIGHT = False

if not USE_REAL_LIGHT:
    az = math.radians(AZIMUTH_DEG)
    el = math.radians(ELEVATION_DEG)
    x  = -math.sin(az) * math.cos(el)
    y  =  math.cos(az) * math.cos(el)
    z  = -math.sin(el)
    light_dir = Vector((x, y, z)).normalized()
    print(f"Virtual light: az={AZIMUTH_DEG}°  el={ELEVATION_DEG}°  "
          f"light_dir={tuple(round(v,4) for v in light_dir)}")

from_sun          = -light_dir
display_light_dir = Vector((from_sun.x, from_sun.z, -from_sun.y))
print(f"display_light_dir = {tuple(round(v,4) for v in display_light_dir)}")

# ── Save state ────────────────────────────────────────────────────────────────

saved = {
    'engine':          render.engine,
    'film_transparent':render.film_transparent,
    'use_border':      render.use_border,
    'res_x':           render.resolution_x,
    'res_y':           render.resolution_y,
    'res_pct':         render.resolution_percentage,
    'filepath':        render.filepath,
    'file_format':     render.image_settings.file_format,
    'light_direction': tuple(scene.display.light_direction),
    'shadow_shift':    scene.display.shadow_shift,
    'view_transform':  scene.view_settings.view_transform,
    'exposure':        scene.view_settings.exposure,
}
ds = scene.display.shading
saved_shading = {a: getattr(ds, a) for a in
    ('type', 'light', 'color_type', 'show_shadows', 'shadow_intensity')
    if hasattr(ds, a)}

# ── Apply settings ────────────────────────────────────────────────────────────

render.engine                     = 'BLENDER_WORKBENCH'
render.film_transparent           = FILM_TRANSPARENT
render.resolution_x               = 512
render.resolution_y               = 512
render.resolution_percentage      = 100
render.filepath                   = OUT_PATH
render.image_settings.file_format = 'PNG'
render.use_border                 = False

scene.display.light_direction      = display_light_dir
scene.display.shadow_shift         = 0.0
scene.view_settings.view_transform = 'Standard'
scene.view_settings.exposure       = EXPOSURE

ds.type             = 'SOLID'
ds.light            = LIGHT_MODE
ds.color_type       = 'SINGLE'
if hasattr(ds, 'single_color'):
    ds.single_color = (1.0, 1.0, 1.0)
ds.show_shadows     = SHOW_SHADOWS
ds.shadow_intensity = 1.0

# ── Render ────────────────────────────────────────────────────────────────────

def img_stats(path, label):
    if not os.path.exists(path):
        print(f"{label}: file not found"); return
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    arr        = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    alpha      = arr[:, :, 3]
    brightness = arr[:, :, :3].mean(axis=2)
    n_shadow   = int(((alpha > 0.5) & (brightness < 0.95)).sum())
    print(f"{label} ({w}x{h}):  brightness [{float(brightness.min()):.3f}, "
          f"{float(brightness.max()):.3f}]  shadow {n_shadow}/{w*h} "
          f"({100*n_shadow/(w*h):.1f}%)")
    bpy.data.images.remove(img)

# ── Full frame ────────────────────────────────────────────────────────────────

render.use_border = False
print(f"Rendering full frame → {OUT_PATH} ...")
bpy.ops.render.render(write_still=True)
img_stats(OUT_PATH, "full frame (no border)")

# ── Border tile (center 25-75%) ───────────────────────────────────────────────

TILE_OUT = "/tmp/shadow_tile_test.png"
render.use_border         = True
if hasattr(render, 'use_crop_to_border'):
    render.use_crop_to_border = True
render.border_min_x = 0.25;  render.border_max_x = 0.75
render.border_min_y = 0.25;  render.border_max_y = 0.75
render.filepath = TILE_OUT
print(f"Rendering border tile (25-75%) → {TILE_OUT} ...")
bpy.ops.render.render(write_still=True)
img_stats(TILE_OUT, "border tile")

    img = bpy.data.images.get('Render Result')
    if img:
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces.active.image = img
                break
        else:
            bpy.ops.render.view_show('INVOKE_DEFAULT')

print("Done.")

# ── Restore state ─────────────────────────────────────────────────────────────

render.engine                     = saved['engine']
render.film_transparent           = saved['film_transparent']
render.use_border                 = saved['use_border']
render.resolution_x               = saved['res_x']
render.resolution_y               = saved['res_y']
render.resolution_percentage      = saved['res_pct']
render.filepath                   = saved['filepath']
render.image_settings.file_format = saved['file_format']
scene.display.light_direction     = saved['light_direction']
scene.display.shadow_shift        = saved['shadow_shift']
scene.view_settings.view_transform = saved['view_transform']
scene.view_settings.exposure      = saved['exposure']
for attr, val in saved_shading.items():
    try:
        setattr(ds, attr, val)
    except Exception:
        pass

print("State restored.")
