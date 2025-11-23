# Optics Table - Multi-Robot Workcell

A Blender 3D model of a multi-robot workcell featuring robot configurations for collaborative automation.

## Contents

- `optics_table.blend` - Main Blender scene file
- `create_optics_table.py` - Python script to generate the workcell model
- `render_optics_table.py` - Script to render the scene
- `franka_description/` - Robot model descriptions
- `optics_table_render.png` - Rendered output

## Usage

### Opening the Model

```bash
blender optics_table.blend
```

### Rendering

```bash
blender -b optics_table.blend -P render_optics_table.py
```

### Creating/Modifying the Model

```bash
blender -b -P create_optics_table.py
```

## Interactive Web Viewer

An interactive web viewer is available to explore this model in 3D directly in your browser.

## Requirements

- Blender 3.0+
- Python 3.x (for scripting)
