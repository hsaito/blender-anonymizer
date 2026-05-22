# Blender Anonymizer

Blender Anonymizer is a small Blender add-on/extension that sanitizes file paths in the currently opened `.blend` file.

It helps when sharing project files by replacing user-specific home directory segments (for example, `C:\\Users\\your-name` or `/home/your-name`) with a configurable placeholder.

## What It Does

- Normalizes file paths to Blender-friendly paths.
- Replaces paths under your home directory with a placeholder (default: `//USER_HOME`).
- Converts non-home absolute paths to project-relative Blender paths when possible.
- Scans text datablocks and replaces any raw home directory string with the placeholder.

### Data Types Covered

The sanitizer currently updates paths in:

- Images (`bpy.data.images`)
- Sounds (`bpy.data.sounds`)
- Movie clips (`bpy.data.movieclips`)
- Linked libraries (`bpy.data.libraries`)
- Active scene render output path (`scene.render.filepath`)
- Sequencer strips with `filepath`
- Text datablocks (`bpy.data.texts`) containing home directory strings

## Installation

This repository currently contains metadata for Blender Extensions (`blender_manifest.toml`) and legacy add-on metadata in `bl_info`.

### Option A: Blender 4.2+ Extension (recommended)

Requirements:

- Blender 4.2 or later

Steps:

1. Package this project as a zip that contains:
	- `blender_manifest.toml`
	- `blender-anonymizer/__init__.py`
2. In Blender, open Extensions and install from local file.
3. Enable the extension if it is not automatically enabled.

### Option B: Legacy Add-on Install

Requirements:

- Blender 3.0+

Steps:

1. Zip the `blender-anonymizer` folder (the one containing `__init__.py`).
2. In Blender: Edit > Preferences > Add-ons > Install...
3. Select the zip and enable Blender Anonymizer.

## Usage

1. Open your `.blend` file.
2. (Optional) Set custom placeholder:
	- Edit > Preferences > Add-ons
	- Find Blender Anonymizer
	- Set **Placeholder for Home Directory** (default: `//USER_HOME`)
3. Run the operator:
	- File > External Data > Sanitize Paths
4. Save the `.blend` file.

## Example

Input path:

```text
C:\Users\alice\Projects\demo\textures\wood.png
```

With placeholder `//USER_HOME`, output becomes:

```text
//USER_HOME/Projects/demo/textures/wood.png
```

## Notes and Limitations

- Changes are applied in-place to the currently opened Blender file data.
- This does not copy/move external files; it only rewrites path strings.
- Relative-path conversion depends on Blender path resolution and your current project location.
- If a path is outside your home directory, it is normalized to Blender relative format when possible.

## Development

Repository layout:

```text
README.md
blender-anonymizer/
  __init__.py
  blender_manifest.toml
```

Main implementation is in `blender-anonymizer/__init__.py`.

## License

GPL-2.0-or-later (see extension metadata).

## Links

- Website: https://github.com/hsaito/blender-anonymizer
- Issues: https://github.com/hsaito/blender-anonymizer/issues
