import bpy 
import math
# import mathutils

_last_view_matrix = None

def matrices_differ(m1, m2, tol=1e-6):
    """Restituisce True se due matrici differiscono oltre la tolleranza."""
    for i in range(4):
        for j in range(4):
            if not math.isclose(m1[i][j], m2[i][j], abs_tol=tol):
                return True
    return False

# a function to monitor the changes of the 3d View
def monitor_view_rotation():
    global _last_view_matrix
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            region_3d = area.spaces.active.region_3d
            current_view = region_3d.view_matrix.copy()
            
            if _last_view_matrix is not None and matrices_differ(current_view, _last_view_matrix):
                pass
                # print("✅ La vista 3D è stata ruotata o spostata!")
            
            _last_view_matrix = current_view
            break
    return 0.1

def start_monitoring():
    if not bpy.app.timers.is_registered(monitor_view_rotation):
        bpy.app.timers.register(monitor_view_rotation)
        print("Monitoraggio vista 3D avviato.")

def stop_monitoring():
    if bpy.app.timers.is_registered(monitor_view_rotation):
        bpy.app.timers.unregister(monitor_view_rotation)
        print("Monitoraggio vista 3D fermato.")
    
def register():
    start_monitoring()

def unregister():
    stop_monitoring()