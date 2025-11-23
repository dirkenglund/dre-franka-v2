import bpy
import math

def inspect_scene():
    print("-" * 40)
    print("SCENE INSPECTION")
    print("-" * 40)
    
    for obj in bpy.context.scene.objects:
        print(f"Object: {obj.name}")
        print(f"  Type: {obj.type}")
        print(f"  Parent: {obj.parent.name if obj.parent else 'None'}")
        print(f"  Location: {obj.location}")
        print(f"  Dimensions: {obj.dimensions}")
        print(f"  Visible: {not obj.hide_viewport}")
        print("-" * 20)

if __name__ == "__main__":
    # Open the file first
    try:
        bpy.ops.wm.open_mainfile(filepath="/Users/englund/.gemini/antigravity/scratch/optics_table.blend")
        inspect_scene()
    except Exception as e:
        print(f"Error opening file: {e}")
