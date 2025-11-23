import bpy
import math
import os

def create_rexroth_gantry(table_width, table_depth, table_height, gantry_height=2.0, offset=(0,0,0), extra_beams_x=None):
    """
    Creates a simple Rexroth-style gantry structure.
    """
    ox, oy, oz = offset
    if extra_beams_x is None:
        extra_beams_x = []
    
    # Profile dimensions (e.g., 80x80mm)
    profile_size = 0.08
    
    mat_alum = bpy.data.materials.get("Rexroth_Alum")
    if not mat_alum:
        mat_alum = bpy.data.materials.new(name="Rexroth_Alum")
        mat_alum.diffuse_color = (0.7, 0.7, 0.75, 1)
        mat_alum.metallic = 0.9
        mat_alum.roughness = 0.3

    def create_profile(name, size, length, location, rotation=(0,0,0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
        obj = bpy.context.active_object
        obj.name = name
        obj.data.materials.append(mat_alum)
        
        # Scale to dimensions
        # Z is length
        obj.scale = (size, size, length)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        obj.location = location
        obj.rotation_euler = rotation
        return obj

    # 4 Vertical Legs
    # Corners of the table assembly
    # Table width is total width (2m). Depth is 3m.
    # Legs should be outside the table? Or bolted to corners?
    # Let's put them just outside.
    
    offset_x = (table_width / 2) + (profile_size / 2)
    offset_y = (table_depth / 2) - (profile_size / 2) # Flush with ends
    
    leg_positions = [
        (offset_x, offset_y),
        (-offset_x, offset_y),
        (offset_x, -offset_y),
        (-offset_x, -offset_y)
    ]
    
    for i, (lx, ly) in enumerate(leg_positions):
        create_profile(f"Gantry_Leg_{i}", profile_size, gantry_height, (ox + lx, oy + ly, oz + gantry_height/2))
        
    # 2 Cross Beams (X-axis) at top
    # Connecting left and right legs at ends
    beam_len_x = table_width + (profile_size * 2)
    create_profile("Gantry_Beam_Front", profile_size, beam_len_x, (ox, oy - offset_y, oz + gantry_height), rotation=(0, math.pi/2, 0))
    create_profile("Gantry_Beam_Back", profile_size, beam_len_x, (ox, oy + offset_y, oz + gantry_height), rotation=(0, math.pi/2, 0))
    
    # 1 Main Longitudinal Beam (Y-axis) in center
    # Connecting front and back beams
    # This holds the robots
    beam_len_y = table_depth
    create_profile("Gantry_Beam_Center", profile_size, beam_len_y, (ox, oy, oz + gantry_height), rotation=(math.pi/2, 0, 0))
    
    # Extra Longitudinal Beams
    for i, bx in enumerate(extra_beams_x):
        create_profile(f"Gantry_Beam_Extra_{i}", profile_size, beam_len_y, (ox + bx, oy, oz + gantry_height), rotation=(math.pi/2, 0, 0))
    
    return oz + gantry_height

def create_optics_table():
    # 1. Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Dimensions
    # Two tables: 1m x 3m each.
    single_table_width = 1.0
    single_table_depth = 3.0
    table_thickness = 0.3
    hole_spacing = 0.025
    leg_height = 0.8
    leg_radius = 0.05 # Slightly thinner legs for individual tables
    
    total_width = single_table_width * 2
    
    # Helper to create one table
    def create_single_table(name_suffix, offset_x):
        # Table Top
        bpy.ops.mesh.primitive_cube_add(
            size=1, 
            location=(offset_x, 0, leg_height + table_thickness / 2)
        )
        table_top = bpy.context.active_object
        table_top.name = f"TableTop_{name_suffix}"
        table_top.scale = (single_table_width, single_table_depth, table_thickness)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Legs
        leg_off_x = (single_table_width / 2) - 0.15
        leg_off_y = (single_table_depth / 2) - 0.15
        
        leg_positions = [
            (offset_x + leg_off_x, leg_off_y),
            (offset_x - leg_off_x, leg_off_y),
            (offset_x + leg_off_x, -leg_off_y),
            (offset_x - leg_off_x, -leg_off_y)
        ]
        
        for i, (lx, ly) in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=leg_radius, 
                depth=leg_height, 
                location=(lx, ly, leg_height / 2)
            )
            leg = bpy.context.active_object
            leg.name = f"Leg_{name_suffix}_{i+1}"
            
        # Holes (Visual)
        hole_radius = 0.003
        hole_depth = 0.001
        
        # Start relative to table center
        start_x_local = -(single_table_width / 2) + 0.05
        start_y_local = -(single_table_depth / 2) + 0.05
        
        # Global start
        start_x = offset_x + start_x_local
        start_y = start_y_local
        
        bpy.ops.mesh.primitive_cylinder_add(
            radius=hole_radius,
            depth=hole_depth,
            location=(start_x, start_y, leg_height + table_thickness - (hole_depth/2) + 0.0001) 
        )
        hole_obj = bpy.context.active_object
        hole_obj.name = f"Hole_Grid_{name_suffix}"
        
        mat_hole = bpy.data.materials.get("Hole_Mat")
        if not mat_hole:
            mat_hole = bpy.data.materials.new(name="Hole_Mat")
            mat_hole.diffuse_color = (0.0, 0.0, 0.0, 1)
            mat_hole.roughness = 1.0
            mat_hole.specular_intensity = 0.0
        hole_obj.data.materials.append(mat_hole)
        
        count_x = int((single_table_width - 0.1) / hole_spacing)
        count_y = int((single_table_depth - 0.1) / hole_spacing)

        mod_x = hole_obj.modifiers.new(name="Array_X", type='ARRAY')
        mod_x.count = count_x
        mod_x.use_relative_offset = False
        mod_x.use_constant_offset = True
        mod_x.constant_offset_displace = (hole_spacing, 0, 0)

        mod_y = hole_obj.modifiers.new(name="Array_Y", type='ARRAY')
        mod_y.count = count_y
        mod_y.use_relative_offset = False
        mod_y.use_constant_offset = True
        mod_y.constant_offset_displace = (0, hole_spacing, 0)
        
        mat_table = bpy.data.materials.get("Table_Mat")
        if not mat_table:
            mat_table = bpy.data.materials.new(name="Table_Mat")
            mat_table.diffuse_color = (0.8, 0.8, 0.8, 1)
            mat_table.roughness = 0.4
            mat_table.metallic = 0.8
        table_top.data.materials.append(mat_table)
        
        return leg_height + table_thickness

    # Create 2 tables
    # Left table (center at -0.5)
    surface_z = create_single_table("Left", -0.5)
    # Right table (center at +0.5)
    create_single_table("Right", 0.5)
    
    # Create Gantry
    gantry_h = create_rexroth_gantry(total_width, single_table_depth, surface_z, gantry_height=2.5)
    
    return surface_z, gantry_h



def create_franka_arm(name_prefix, location, rotation_z=0):
    """
    Creates a Franka FR3 arm by importing DAE meshes.
    Uses a Frame (Empty) + Mesh hierarchy to preserve DAE visual offsets.
    """
    import os
    
    # Base path
    base_path = os.path.join(os.path.dirname(__file__), "franka_description/meshes")
    arm_path = os.path.join(base_path, "robot_arms/fr3/visual")
    hand_path = os.path.join(base_path, "robot_ee/franka_hand_white/visual")
    
    # Kinematics from YAML (hardcoded here for simplicity)
    # xyz, rpy (radians)
    joints = {
        'joint1': {'xyz': (0, 0, 0.333), 'rpy': (0, 0, 0)},
        'joint2': {'xyz': (0, 0, 0), 'rpy': (-1.57079632679, 0, 0)},
        'joint3': {'xyz': (0, -0.316, 0), 'rpy': (1.57079632679, 0, 0)},
        'joint4': {'xyz': (0.0825, 0, 0), 'rpy': (1.57079632679, 0, 0)},
        'joint5': {'xyz': (-0.0825, 0.384, 0), 'rpy': (-1.57079632679, 0, 0)},
        'joint6': {'xyz': (0, 0, 0), 'rpy': (1.57079632679, 0, 0)},
        'joint7': {'xyz': (0.088, 0, 0), 'rpy': (1.57079632679, 0, 0)},
        'joint8': {'xyz': (0, 0, 0.107), 'rpy': (0, 0, 0)}, # Flange
    }

    def create_link_frame(name, parent, xyz, rpy):
        # Create an Empty to represent the Joint/Link Frame
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.05, location=(0,0,0))
        frame = bpy.context.active_object
        frame.name = name
        
        if parent:
            frame.parent = parent
            frame.location = xyz
            frame.rotation_euler = rpy
        else:
            frame.location = location
            frame.rotation_euler = (0, 0, rotation_z)
            
        return frame

    def import_mesh_to_frame(file_path, frame, name):
        if not os.path.exists(file_path):
            print(f"Warning: Mesh not found: {file_path}")
            return
            
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.wm.collada_import(filepath=file_path)
        imported = bpy.context.selected_objects
        
        if not imported:
            return
            
        # Apply Scale ONLY (0.001 -> 1.0)
        # But DO NOT apply Location/Rotation, as that burns the DAE offset into the mesh vertices
        # and resets origin to 0,0,0, which is what we want IF we parent to frame.
        # Wait, if we parent to frame, we want the mesh to keep its local offset relative to frame.
        # The DAE import sets obj.location to the offset.
        # So we just parent.
        
        # However, we MUST fix the scale (0.001).
        # If we apply scale, it scales the location offset too? Yes.
        # So:
        # 1. Parent to Frame.
        # 2. Apply Scale.
        
        root_obj = imported[0]
        if len(imported) > 1:
            bpy.context.view_layer.objects.active = root_obj
            bpy.ops.object.join()
            root_obj = bpy.context.active_object
            
        root_obj.name = name
        root_obj.parent = frame
        
        # The DAE import might have set a global scale 0.001.
        # We want to apply this scale so the object is 1.0 but small.
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        return root_obj

    # --- Assembly ---
    
    # Link 0 (Base)
    # Frame is at robot base location
    f0 = create_link_frame(f"{name_prefix}_L0_Frame", None, (0,0,0), (0,0,0))
    import_mesh_to_frame(os.path.join(arm_path, "link0.dae"), f0, f"{name_prefix}_link0_mesh")
    
    # Link 1
    f1 = create_link_frame(f"{name_prefix}_L1_Frame", f0, joints['joint1']['xyz'], joints['joint1']['rpy'])
    import_mesh_to_frame(os.path.join(arm_path, "link1.dae"), f1, f"{name_prefix}_link1_mesh")
    
    # Link 2
    f2 = create_link_frame(f"{name_prefix}_L2_Frame", f1, joints['joint2']['xyz'], joints['joint2']['rpy'])
    import_mesh_to_frame(os.path.join(arm_path, "link2.dae"), f2, f"{name_prefix}_link2_mesh")
    
    # Link 3
    f3 = create_link_frame(f"{name_prefix}_L3_Frame", f2, joints['joint3']['xyz'], joints['joint3']['rpy'])
    import_mesh_to_frame(os.path.join(arm_path, "link3.dae"), f3, f"{name_prefix}_link3_mesh")
    
    # Link 4
    f4 = create_link_frame(f"{name_prefix}_L4_Frame", f3, joints['joint4']['xyz'], joints['joint4']['rpy'])
    import_mesh_to_frame(os.path.join(arm_path, "link4.dae"), f4, f"{name_prefix}_link4_mesh")
    
    # Link 5
    f5 = create_link_frame(f"{name_prefix}_L5_Frame", f4, joints['joint5']['xyz'], joints['joint5']['rpy'])
    import_mesh_to_frame(os.path.join(arm_path, "link5.dae"), f5, f"{name_prefix}_link5_mesh")
    
    # Link 6
    f6 = create_link_frame(f"{name_prefix}_L6_Frame", f5, joints['joint6']['xyz'], joints['joint6']['rpy'])
    import_mesh_to_frame(os.path.join(arm_path, "link6.dae"), f6, f"{name_prefix}_link6_mesh")
    
    # Link 7
    f7 = create_link_frame(f"{name_prefix}_L7_Frame", f6, joints['joint7']['xyz'], joints['joint7']['rpy'])
    import_mesh_to_frame(os.path.join(arm_path, "link7.dae"), f7, f"{name_prefix}_link7_mesh")
    
    # Hand (Flange)
    f_hand = create_link_frame(f"{name_prefix}_Hand_Frame", f7, joints['joint8']['xyz'], joints['joint8']['rpy'])
    # Hand mesh usually needs rotation? 
    # In franka_hand.xacro, the hand joint is fixed.
    # Let's import hand.dae. It might need -45 deg rotation (pi/4) as seen in some configs, or it aligns naturally.
    # The kinematics.yaml has joint8 (flange).
    # The hand is attached to the flange.
    # Usually hand.dae origin is at the mounting plate.
    # Let's try importing without extra rotation first, or check xacro.
    # franka_arm.xacro: <joint name="${prefix}joint8" type="fixed"> ... <child link="${prefix}link8" />
    # Then hand is attached to link8?
    # Actually, `fr3.urdf.xacro` includes `franka_hand.xacro` connected to `link8`.
    # <xacro:franka_hand connected_to="fr3_link8" safety_distance="0.03"/>
    # In `franka_hand.xacro`:
    # <joint name="${ns}_hand_joint" type="fixed">
    #   <parent link="${connected_to}"/>
    #   <child link="${ns}_hand"/>
    #   <origin xyz="0 0 0" rpy="0 0 ${pi/4}"/>
    # </joint>
    # So Hand is rotated 45 degrees (pi/4) relative to Flange (Link 8).
    
    # Create Hand Frame
    f_hand_actual = create_link_frame(f"{name_prefix}_Hand_Actual_Frame", f_hand, (0,0,0), (0, 0, math.pi/4))
    import_mesh_to_frame(os.path.join(hand_path, "hand.dae"), f_hand_actual, f"{name_prefix}_hand_mesh")
    
    # Fingers
    # Finger joint: prismatic.
    # <axis xyz="0 0 1" /> ? No, usually Y or X.
    # In `franka_hand.xacro`:
    # <joint name="${ns}_finger_joint1" type="prismatic">
    #   <origin xyz="0 0 0.0584" rpy="0 0 0"/>
    #   <axis xyz="0 1 0"/>
    # </joint>
    # <joint name="${ns}_finger_joint2" type="prismatic">
    #   <origin xyz="0 0 0.0584" rpy="0 0 ${pi}"/>
    #   <axis xyz="0 1 0"/>
    # </joint>
    
    f_finger1 = create_link_frame(f"{name_prefix}_Finger1_Frame", f_hand_actual, (0, 0, 0.0584), (0,0,0))
    import_mesh_to_frame(os.path.join(hand_path, "finger.dae"), f_finger1, f"{name_prefix}_finger1_mesh")
    
    f_finger2 = create_link_frame(f"{name_prefix}_Finger2_Frame", f_hand_actual, (0, 0, 0.0584), (0, 0, math.pi))
    import_mesh_to_frame(os.path.join(hand_path, "finger.dae"), f_finger2, f"{name_prefix}_finger2_mesh")

    return f0

def create_reach_sphere(location):
    """
    Creates a semi-transparent sphere representing the robot's reach.
    Franka FR3 reach is ~855mm.
    """
    radius = 0.855
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    sphere = bpy.context.active_object
    sphere.name = "Reach_Sphere"
    
    mat_reach = bpy.data.materials.get("Reach_Mat")
    if not mat_reach:
        mat_reach = bpy.data.materials.new(name="Reach_Mat")
        mat_reach.use_nodes = True
        bsdf = mat_reach.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0.0, 0.5, 1.0, 1.0) # Blueish
        bsdf.inputs["Alpha"].default_value = 0.15
        bsdf.inputs["Roughness"].default_value = 0.1
        # Blender 4.2+ Eevee Next handles transparency differently (Raytraced)
        # Old properties like blend_method and shadow_method are deprecated/removed
        # mat_reach.blend_method = 'BLEND' 
        # mat_reach.shadow_method = 'NONE'
        
    sphere.data.materials.append(mat_reach)
    
    # Smooth shade
    bpy.ops.object.shade_smooth()
    
    return sphere

if __name__ == "__main__":
    # Create Tables
    # We need 4 tables now.
    # Center ones: +/- 0.5
    # Outer ones: +/- 1.5
    
    # We need to modify create_optics_table to accept offsets or just call create_single_table loop?
    # Let's modify create_optics_table to be more flexible or just hack it here?
    # create_optics_table clears the scene.
    # Let's update create_optics_table inside the function to do 4 tables.
    pass

def create_human_proxy(location, height=1.75, rotation_z=0):
    """
    Creates a blocky human figure with variable height and reach visualization.
    Parts overlap to avoid gaps.
    """
    ox, oy, oz = location
    
    # Proportional Dimensions
    # Standard ratios based on height
    head_size = height * 0.07
    torso_height = height * 0.28
    leg_height = height * 0.48
    
    # Widths/Depths (scaled slightly with height but not fully linear to keep proportions reasonable)
    scale = height / 1.75
    torso_width = 0.35 * scale
    torso_depth = 0.2 * scale
    limb_width = 0.1 * scale
    arm_len = height * 0.38
    
    overlap = 0.03 # 3cm overlap to prevent gaps
    
    mat_human = bpy.data.materials.get("Human_Mat")
    if not mat_human:
        mat_human = bpy.data.materials.new(name="Human_Mat")
        mat_human.diffuse_color = (0.8, 0.6, 0.4, 1) # Skin-ish
        
    mat_shirt = bpy.data.materials.get("Human_Shirt")
    if not mat_shirt:
        mat_shirt = bpy.data.materials.new(name="Human_Shirt")
        mat_shirt.diffuse_color = (0.2, 0.2, 0.8, 1) # Blue shirt

    mat_pants = bpy.data.materials.get("Human_Pants")
    if not mat_pants:
        mat_pants = bpy.data.materials.new(name="Human_Pants")
        mat_pants.diffuse_color = (0.1, 0.1, 0.1, 1) # Dark pants

    def create_part(name, size, loc, mat):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0)) # Create at origin first
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = size
        bpy.ops.object.transform_apply(scale=True)
        obj.data.materials.append(mat)
        obj.location = loc
        return obj

    # Legs
    # Center of leg is at z = leg_height/2
    # Add overlap to top of legs (into torso)
    leg_z = oz + leg_height/2
    leg_l = create_part("Leg_L", (limb_width, limb_width, leg_height + overlap), (ox - 0.1*scale, oy, leg_z), mat_pants)
    leg_r = create_part("Leg_R", (limb_width, limb_width, leg_height + overlap), (ox + 0.1*scale, oy, leg_z), mat_pants)
    
    # Torso
    # Starts at leg_height. Center is leg_height + torso_height/2
    # Overlaps down into legs and up into head/arms
    torso_z = oz + leg_height + torso_height/2
    torso = create_part("Torso", (torso_width, torso_depth, torso_height + overlap), (ox, oy, torso_z), mat_shirt)
    
    # Head
    # Center is at top of torso + radius
    # Overlap is handled by sphere penetrating torso
    head_z = oz + leg_height + torso_height + head_size - overlap
    bpy.ops.mesh.primitive_uv_sphere_add(radius=head_size, location=(ox, oy, head_z))
    head = bpy.context.active_object
    head.name = "Head"
    head.data.materials.append(mat_human)
    
    # Arms (Resting at sides)
    # Shoulder height
    shoulder_z = oz + leg_height + torso_height - (0.05 * scale)
    arm_z = shoulder_z - arm_len/2
    
    arm_l = create_part("Arm_L", (limb_width, limb_width, arm_len), (ox - torso_width/2 - limb_width/2 + overlap, oy, arm_z), mat_shirt)
    arm_r = create_part("Arm_R", (limb_width, limb_width, arm_len), (ox + torso_width/2 + limb_width/2 - overlap, oy, arm_z), mat_shirt)
    
    # Join Body
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [leg_l, leg_r, torso, head, arm_l, arm_r]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.join()
    human = bpy.context.active_object
    human.name = f"Human_Proxy_{height}m"
    
    # Apply Rotation
    human.rotation_euler = (0, 0, rotation_z)
    
    # Reach Sphere (Human)
    # Radius ~0.8m, centered at shoulder height
    # Adjust reach radius slightly with height?
    reach_radius = 0.8 * scale
    # Reach location needs to be rotated too!
    # Default reach is forward (+Y relative to human?)
    # Wait, create_human_proxy builds along X/Y axes assuming facing Y?
    # No, torso width is X, depth is Y. So facing Y (or -Y).
    # Reach loc was (ox, oy + 0.3, shoulder_z). This implies facing +Y.
    
    # We need to calculate the rotated reach location.
    # Relative offset: (0, 0.3, 0)
    # Rotate this offset by rotation_z
    
    rel_x = 0
    rel_y = 0.3
    
    rot_x = rel_x * math.cos(rotation_z) - rel_y * math.sin(rotation_z)
    rot_y = rel_x * math.sin(rotation_z) + rel_y * math.cos(rotation_z)
    
    reach_loc = (ox + rot_x, oy + rot_y, shoulder_z)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=reach_radius, location=reach_loc)
    sphere = bpy.context.active_object
    sphere.name = f"Human_Reach_Sphere_{height}m"
    
    mat_reach = bpy.data.materials.get("Human_Reach_Mat")
    if not mat_reach:
        mat_reach = bpy.data.materials.new(name="Human_Reach_Mat")
        mat_reach.use_nodes = True
        bsdf = mat_reach.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (1.0, 0.5, 0.0, 1.0) # Orange
        bsdf.inputs["Alpha"].default_value = 0.15
        bsdf.inputs["Roughness"].default_value = 0.1
        
    sphere.data.materials.append(mat_reach)
    bpy.ops.object.shade_smooth()
    
    return human

def create_workcell(origin_offset, cell_index, config="mixed"):
    """
    Creates a full workcell (4 tables, gantry, 6 robots) at a given offset.
    config: "mixed" (4 edge, 2 susp) or "all_suspended" (6 susp)
    """
    ox, oy, oz = origin_offset
    
    # Dimensions
    inner_table_width = 2.0 # Full width (was 2x 1.0)
    inner_table_depth = 1.5 # Half depth (was 3.0)
    outer_table_width = 0.6 
    outer_table_depth = 1.5 # Match inner depth
    
    table_thickness = 0.3
    hole_spacing = 0.025
    leg_height = 0.92 # Total height = 0.92 + 0.3 = 1.22m (~4ft)
    leg_radius = 0.05
    
    gap_y = 0.1 # Gap between front/back tables (Seam)
    gap_x = 0.3 # Gap between inner/outer tables (Aisle)
    
    # Calculate positions relative to workcell center (ox, oy)
    
    # Y Offsets for Front/Back
    # Center Y = +/- (depth/2 + gap_y/2)
    offset_y_front = -(inner_table_depth / 2) - (gap_y / 2)
    offset_y_back = (inner_table_depth / 2) + (gap_y / 2)
    
    # X Offsets for Outer Tables
    # Inner edge of outer table = inner_width/2 + gap_x
    # Center X = inner_width/2 + gap_x + outer_width/2
    offset_x_outer_right = (inner_table_width / 2) + gap_x + (outer_table_width / 2)
    offset_x_outer_left = -offset_x_outer_right
    
    # Total width for gantry
    # Outer edge = offset_x_outer_right + outer_width/2
    total_width_half = offset_x_outer_right + (outer_table_width / 2)
    total_width = total_width_half * 2
    
    # Helper for single table (modified to take width AND depth)
    def create_single_table(name_suffix, local_x, local_y, width, depth):
        # Global location
        gx = ox + local_x
        gy = oy + local_y
        gz = oz
        
        # Table Top
        bpy.ops.mesh.primitive_cube_add(
            size=1, 
            location=(gx, gy, gz + leg_height + table_thickness / 2)
        )
        table_top = bpy.context.active_object
        table_top.name = f"TableTop_{cell_index}_{name_suffix}"
        table_top.scale = (width, depth, table_thickness)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Legs
        leg_off_x = (width / 2) - 0.1
        leg_off_y = (depth / 2) - 0.15
        
        leg_positions = [
            (gx + leg_off_x, gy + leg_off_y),
            (gx - leg_off_x, gy + leg_off_y),
            (gx + leg_off_x, gy - leg_off_y),
            (gx - leg_off_x, gy - leg_off_y)
        ]
        
        for i, (lx, ly) in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=leg_radius, 
                depth=leg_height, 
                location=(lx, ly, gz + leg_height / 2)
            )
            leg = bpy.context.active_object
            leg.name = f"Leg_{cell_index}_{name_suffix}_{i+1}"
            
        # Holes (Visual)
        hole_radius = 0.003
        hole_depth = 0.001
        
        # Start relative to table center
        start_x_local = -(width / 2) + 0.05
        start_y_local = -(depth / 2) + 0.05
        
        # Global start
        start_x = gx + start_x_local
        start_y = gy + start_y_local
        
        bpy.ops.mesh.primitive_cylinder_add(
            radius=hole_radius,
            depth=hole_depth,
            location=(start_x, start_y, gz + leg_height + table_thickness - (hole_depth/2) + 0.0001) 
        )
        hole_obj = bpy.context.active_object
        hole_obj.name = f"Hole_Grid_{cell_index}_{name_suffix}"
        
        mat_hole = bpy.data.materials.get("Hole_Mat")
        if not mat_hole:
            mat_hole = bpy.data.materials.new(name="Hole_Mat")
            mat_hole.diffuse_color = (0.0, 0.0, 0.0, 1)
            mat_hole.roughness = 1.0
            mat_hole.specular_intensity = 0.0
        hole_obj.data.materials.append(mat_hole)
        
        count_x = int((width - 0.1) / hole_spacing)
        count_y = int((depth - 0.1) / hole_spacing)

        mod_x = hole_obj.modifiers.new(name="Array_X", type='ARRAY')
        mod_x.count = count_x
        mod_x.use_relative_offset = False
        mod_x.use_constant_offset = True
        mod_x.constant_offset_displace = (hole_spacing, 0, 0)

        mod_y = hole_obj.modifiers.new(name="Array_Y", type='ARRAY')
        mod_y.count = count_y
        mod_y.use_relative_offset = False
        mod_y.use_constant_offset = True
        mod_y.constant_offset_displace = (0, hole_spacing, 0)
        
        mat_table = bpy.data.materials.get("Table_Mat")
        if not mat_table:
            mat_table = bpy.data.materials.new(name="Table_Mat")
            mat_table.diffuse_color = (0.8, 0.8, 0.8, 1)
            mat_table.roughness = 0.4
            mat_table.metallic = 0.8
        table_top.data.materials.append(mat_table)
        
        return leg_height + table_thickness

    # Create Tables (End-to-End Stacking)
    
    # Inner Tables (2m wide, 1.5m deep)
    surface_z = create_single_table("Inner_Front", 0, offset_y_front, inner_table_width, inner_table_depth)
    create_single_table("Inner_Back", 0, offset_y_back, inner_table_width, inner_table_depth)
    
    # Outer Tables (0.6m wide, 1.5m deep) - Split to match seams
    # Left Side
    create_single_table("Outer_L_Front", offset_x_outer_left, offset_y_front, outer_table_width, outer_table_depth)
    create_single_table("Outer_L_Back", offset_x_outer_left, offset_y_back, outer_table_width, outer_table_depth)
    
    # Right Side
    create_single_table("Outer_R_Front", offset_x_outer_right, offset_y_front, outer_table_width, outer_table_depth)
    create_single_table("Outer_R_Back", offset_x_outer_right, offset_y_back, outer_table_width, outer_table_depth)
    
    # --- Robot Placement Logic ---
    
    # Define X positions for side robots
    # Inner table width is 2.0. Edge is at +/- 1.0.
    # Place inboard 0.15m -> +/- 0.85.
    edge_x = (inner_table_width / 2) - 0.15
    
    extra_beams = []
    if config == "all_suspended":
        extra_beams = [edge_x, -edge_x]
    
    # Create Gantry
    # Total depth is 3m + gap_y.
    total_depth = (inner_table_depth * 2) + gap_y
    gantry_h = create_rexroth_gantry(total_width, total_depth, surface_z, gantry_height=2.5, offset=(ox, oy, oz), extra_beams_x=extra_beams)
    
    # Drop strut length
    drop_len = 0.5
    
    def create_strut(name, loc):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = (0.08, 0.08, drop_len)
        bpy.ops.object.transform_apply(scale=True)
        obj.location = (loc[0], loc[1], loc[2] - drop_len/2)
        mat = bpy.data.materials.get("Rexroth_Alum")
        if mat: obj.data.materials.append(mat)
        return obj
    
    # Suspended Z (bottom of beam)
    susp_z = gantry_h - 0.04 
    
    if config == "mixed":
        # --- Mixed Config: 4 Edge, 2 Center Suspended ---
        
        # Edge Robots (Table Mounted)
        # Left Side
        create_franka_arm(f"R_Edge_L1_{cell_index}", location=(ox - edge_x, oy + 0.75, surface_z), rotation_z=0)
        create_reach_sphere((ox - edge_x, oy + 0.75, surface_z + 0.333))
        
        create_franka_arm(f"R_Edge_L2_{cell_index}", location=(ox - edge_x, oy - 0.75, surface_z), rotation_z=0)
        create_reach_sphere((ox - edge_x, oy - 0.75, surface_z + 0.333))
        
        # Right Side
        create_franka_arm(f"R_Edge_R1_{cell_index}", location=(ox + edge_x, oy + 0.75, surface_z), rotation_z=math.pi)
        create_reach_sphere((ox + edge_x, oy + 0.75, surface_z + 0.333))
        
        create_franka_arm(f"R_Edge_R2_{cell_index}", location=(ox + edge_x, oy - 0.75, surface_z), rotation_z=math.pi)
        create_reach_sphere((ox + edge_x, oy - 0.75, surface_z + 0.333))
        
        # Center Suspended Robots
        # Susp 1
        create_strut(f"Strut_1_{cell_index}", (ox, oy + 0.5, susp_z))
        r_susp_1 = create_franka_arm(f"R_Susp_1_{cell_index}", location=(ox, oy + 0.5, susp_z - drop_len), rotation_z=0)
        r_susp_1.rotation_euler = (math.pi, 0, 0)
        create_reach_sphere((ox, oy + 0.5, susp_z - drop_len - 0.333))
        
        # Susp 2
        create_strut(f"Strut_2_{cell_index}", (ox, oy - 0.5, susp_z))
        r_susp_2 = create_franka_arm(f"R_Susp_2_{cell_index}", location=(ox, oy - 0.5, susp_z - drop_len), rotation_z=0)
        r_susp_2.rotation_euler = (math.pi, 0, math.pi)
        create_reach_sphere((ox, oy - 0.5, susp_z - drop_len - 0.333))
        
    elif config == "all_suspended":
        # --- All Suspended Config: 6 Suspended Robots ---
        
        # Center Suspended (Same as mixed)
        # Susp 1
        create_strut(f"Strut_C1_{cell_index}", (ox, oy + 0.5, susp_z))
        r_susp_1 = create_franka_arm(f"R_Susp_C1_{cell_index}", location=(ox, oy + 0.5, susp_z - drop_len), rotation_z=0)
        r_susp_1.rotation_euler = (math.pi, 0, 0)
        create_reach_sphere((ox, oy + 0.5, susp_z - drop_len - 0.333))
        
        # Susp 2
        create_strut(f"Strut_C2_{cell_index}", (ox, oy - 0.5, susp_z))
        r_susp_2 = create_franka_arm(f"R_Susp_C2_{cell_index}", location=(ox, oy - 0.5, susp_z - drop_len), rotation_z=0)
        r_susp_2.rotation_euler = (math.pi, 0, math.pi)
        create_reach_sphere((ox, oy - 0.5, susp_z - drop_len - 0.333))
        
        # Side Suspended (Replacing Edge Robots)
        # Locations match edge X/Y, but at susp_z
        
        # Left Side Beams (x = -edge_x)
        # Susp L1
        create_strut(f"Strut_L1_{cell_index}", (ox - edge_x, oy + 0.75, susp_z))
        r_susp_l1 = create_franka_arm(f"R_Susp_L1_{cell_index}", location=(ox - edge_x, oy + 0.75, susp_z - drop_len), rotation_z=0)
        r_susp_l1.rotation_euler = (math.pi, 0, 0)
        create_reach_sphere((ox - edge_x, oy + 0.75, susp_z - drop_len - 0.333))
        
        # Susp L2
        create_strut(f"Strut_L2_{cell_index}", (ox - edge_x, oy - 0.75, susp_z))
        r_susp_l2 = create_franka_arm(f"R_Susp_L2_{cell_index}", location=(ox - edge_x, oy - 0.75, susp_z - drop_len), rotation_z=0)
        r_susp_l2.rotation_euler = (math.pi, 0, 0)
        create_reach_sphere((ox - edge_x, oy - 0.75, susp_z - drop_len - 0.333))
        
        # Right Side Beams (x = +edge_x)
        # Susp R1
        create_strut(f"Strut_R1_{cell_index}", (ox + edge_x, oy + 0.75, susp_z))
        r_susp_r1 = create_franka_arm(f"R_Susp_R1_{cell_index}", location=(ox + edge_x, oy + 0.75, susp_z - drop_len), rotation_z=0)
        r_susp_r1.rotation_euler = (math.pi, 0, math.pi)
        create_reach_sphere((ox + edge_x, oy + 0.75, susp_z - drop_len - 0.333))
        
        # Susp R2
        create_strut(f"Strut_R2_{cell_index}", (ox + edge_x, oy - 0.75, susp_z))
        r_susp_r2 = create_franka_arm(f"R_Susp_R2_{cell_index}", location=(ox + edge_x, oy - 0.75, susp_z - drop_len), rotation_z=0)
        r_susp_r2.rotation_euler = (math.pi, 0, math.pi)
        create_reach_sphere((ox + edge_x, oy - 0.75, susp_z - drop_len - 0.333))


def create_optics_table():
    # 1. Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Create Workcell 1 (Mixed Config)
    # Offset X = -2.5 (Left side)
    create_workcell((-2.5, 0, 0), 1, config="mixed")
    
    # Create Workcell 2 (All Suspended Config)
    # Offset X = +2.5 (Right side)
    # Walkway in between is 5m center-to-center.
    # Each cell is ~4m wide (+/- 2m).
    # If centers are at +/- 2.5:
    # Cell 1 right edge: -2.5 + 2 = -0.5
    # Cell 2 left edge: 2.5 - 2 = 0.5
    # Gap = 1.0m. Good for walkway.
    create_workcell((2.5, 0, 0), 2, config="all_suspended")
    
    # Calculate Gap Centers for Human Placement
    # Gap is between Inner and Outer tables.
    # Inner table edge (from center of workcell): +/- 2.05
    # Outer table edge (from center of workcell): +/- 2.35
    # Gap center: +/- 2.20
    
    # Workcell 1 Center: -2.5
    # Left Gap: -2.5 - 2.20 = -4.70
    # Right Gap: -2.5 + 2.20 = -0.30
    
    # Workcell 2 Center: +2.5
    # Left Gap: 2.5 - 2.20 = 0.30
    # Right Gap: 2.5 + 2.20 = 4.70
    
    # Walkway Center: 0.0
    
    # Add Humans (Varying Heights & Rotations)
    
    # 1. In the central walkway (wide gap, rotation doesn't matter much, but let's face Y)
    create_human_proxy((0, 0, 0), height=1.75, rotation_z=0) 
    
    # 2. In the narrow gap of Workcell 1 (Right side of cell 1)
    # Location: -0.30
    # Rotation: 90 deg (pi/2) to face along the aisle (Y axis)
    create_human_proxy((-0.30, 2, 0), height=1.85, rotation_z=math.pi/2)
    
    # 3. In the narrow gap of Workcell 2 (Left side of cell 2)
    # Location: 0.30
    # Rotation: -90 deg (-pi/2)
    create_human_proxy((0.30, -1, 0), height=1.65, rotation_z=-math.pi/2)
    
    # 4. Maybe one in the outer gap?
    # Location: -4.70
    create_human_proxy((-4.70, 0, 0), height=1.70, rotation_z=math.pi/2)

if __name__ == "__main__":
    create_optics_table()
    
    # Save
    output_path = os.path.abspath("optics_table.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"Saved to {output_path}")



