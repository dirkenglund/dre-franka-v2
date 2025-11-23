import bpy
import math
import os

def render_table():
    # Open the existing file
    blend_file_path = os.path.abspath("optics_table.blend")
    bpy.ops.wm.open_mainfile(filepath=blend_file_path)

    # Add Camera
    # Table center is roughly 0,0,0.8+0.15 = ~0.95m high
    # Position camera to view from isometric-ish angle
    # Moved back further for duplicated scene (two workcells + walkway)
    # Total width ~10m.
    camera_loc = (8, -10, 6)
    bpy.ops.object.camera_add(location=camera_loc)
    camera = bpy.context.active_object
    camera.rotation_mode = 'XYZ'
    # Point camera at center (roughly)
    # Manual rotation for (8, -10, 6) looking at (0,0,1)
    import mathutils
    look_at = mathutils.Vector((0, 0, 1))
    direction = look_at - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    bpy.context.scene.camera = camera

    # Add Light (Sun)
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    # Point sun roughly at table
    direction_sun = mathutils.Vector((0, 0, 0)) - sun.location
    rot_quat_sun = direction_sun.to_track_quat('-Z', 'Y')
    sun.rotation_euler = rot_quat_sun.to_euler()

    # Add Fill Light (Area)
    bpy.ops.object.light_add(type='AREA', location=(-3, -3, 5))
    fill = bpy.context.active_object
    fill.data.energy = 500.0
    fill.data.size = 5.0
    direction_fill = mathutils.Vector((0, 0, 0)) - fill.location
    rot_quat_fill = direction_fill.to_track_quat('-Z', 'Y')
    fill.rotation_euler = rot_quat_fill.to_euler()

    # Render Settings
    bpy.context.scene.render.engine = 'CYCLES' # Cycles handles transparency/transmission much better
    # bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT' 
    
    # Cycles settings for speed
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.use_denoising = True 
    
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 768
    bpy.context.scene.render.filepath = os.path.abspath("optics_table_render.png")

    # Render
    bpy.ops.render.render(write_still=True)
    print(f"Rendered to {bpy.context.scene.render.filepath}")

if __name__ == "__main__":
    render_table()
