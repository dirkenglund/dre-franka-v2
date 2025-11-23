import bpy
import os

def debug_import():
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Path to link1
    file_path = os.path.abspath("franka_description/meshes/robot_arms/fr3/visual/link1.dae")
    
    print(f"Importing {file_path}")
    bpy.ops.wm.collada_import(filepath=file_path)
    
    print("Imported Objects:")
    for obj in bpy.context.selected_objects:
        print(f"  Name: {obj.name}")
        print(f"  Type: {obj.type}")
        print(f"  Parent: {obj.parent.name if obj.parent else 'None'}")
        print(f"  Location: {obj.location}")
        print(f"  Dimensions: {obj.dimensions}")
        print(f"  Scale: {obj.scale}")
        if obj.type == 'MESH':
            print(f"  Vertices: {len(obj.data.vertices)}")
        print("-" * 10)

if __name__ == "__main__":
    debug_import()
