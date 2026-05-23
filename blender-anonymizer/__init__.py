bl_info = {
    "name": "Blender Anonymizer",
    "author": "Hideki Saito",
    "version": (1, 1, 0),
    "blender": (3, 0, 0),
    "location": "File > External Data > Sanitize Paths",
    "description": "Normalize and anonymize file paths in the current .blend",
    "category": "System",
}

import bpy
import os
import re


# ==============================
# Addon Preferences
# ==============================

class SanitizePathsPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    home_placeholder: bpy.props.StringProperty(
        name="Placeholder for Home Directory",
        description="String used to replace the user's home directory in paths",
        default="//USER_HOME",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "home_placeholder")


# ==============================
# Core Logic
# ==============================

HOME_DIR = os.path.expanduser("~")


def _is_datablock_packed(datablock) -> bool:
    """Best-effort packed check for datablocks that support packing."""
    packed_file = getattr(datablock, "packed_file", None)
    if packed_file is not None:
        return True

    packed_files = getattr(datablock, "packed_files", None)
    if packed_files:
        try:
            return len(packed_files) > 0
        except Exception:
            return True

    return False


def find_non_packed_references():
    """Collect external data references that are not packed into the .blend file."""
    refs = []

    for img in bpy.data.images:
        if img.source == 'FILE' and img.filepath and not _is_datablock_packed(img):
            refs.append(f"Image: {img.name}")

    for snd in bpy.data.sounds:
        if snd.filepath and not _is_datablock_packed(snd):
            refs.append(f"Sound: {snd.name}")

    for clip in bpy.data.movieclips:
        if clip.filepath and not _is_datablock_packed(clip):
            refs.append(f"Movie Clip: {clip.name}")

    for lib in bpy.data.libraries:
        if lib.filepath:
            refs.append(f"Library: {lib.filepath}")

    scene = bpy.context.scene
    seq = scene.sequence_editor
    if seq:
        if hasattr(seq, "sequences_all"):
            strips = seq.sequences_all
        elif hasattr(seq, "sequences"):
            strips = seq.sequences
        else:
            strips = []

        for strip in strips:
            if hasattr(strip, "filepath") and strip.filepath:
                refs.append(f"Sequencer Strip: {strip.name}")

    return refs


def sanitize_path(path: str, placeholder: str) -> str:
    """Normalize and anonymize paths containing user-specific information (robust version)"""
    if not path:
        return path

    try:
        abs_path = bpy.path.abspath(path)
    except Exception:
        # For paths that Blender cannot resolve, return as is
        return path

    # Home directory → Placeholder
    if abs_path.startswith(HOME_DIR):
        rel_from_home = os.path.relpath(abs_path, HOME_DIR)
        return os.path.join(placeholder, rel_from_home)

    # .blend file location
    blend_dir = os.path.dirname(bpy.data.filepath)

    # If .blend is unsaved, cannot make relative paths
    if not blend_dir:
        return abs_path

    # If on a different drive, cannot make relative paths, return absolute path
    if os.path.splitdrive(abs_path)[0].lower() != os.path.splitdrive(blend_dir)[0].lower():
        return abs_path  # <- This one's important

    # Convert to relative path (safely handle exceptions)
    try:
        rel = bpy.path.relpath(abs_path)
        return rel
    except ValueError:
        # If relpath fails, return absolute path
        return abs_path
    except Exception:
        return abs_path


def sanitize_all_paths(placeholder: str):
    """Normalize all data block paths"""
    # Images
    for img in bpy.data.images:
        if img.source == 'FILE' and img.filepath:
            img.filepath = sanitize_path(img.filepath, placeholder)

    # Sounds
    for snd in bpy.data.sounds:
        if snd.filepath:
            snd.filepath = sanitize_path(snd.filepath, placeholder)

    # Movie Clips
    for clip in bpy.data.movieclips:
        if clip.filepath:
            clip.filepath = sanitize_path(clip.filepath, placeholder)

    # Libraries
    for lib in bpy.data.libraries:
        if lib.filepath:
            lib.filepath = sanitize_path(lib.filepath, placeholder)

    # Render Output
    scene = bpy.context.scene
    if scene.render.filepath:
        scene.render.filepath = sanitize_path(scene.render.filepath, placeholder)

    # Sequencer
    seq = scene.sequence_editor
    if seq:
        # Blender 4.x: sequences_all
        if hasattr(seq, "sequences_all"):
            strips = seq.sequences_all
        # Blender 5.x: sequences
        elif hasattr(seq, "sequences"):
            strips = seq.sequences
        # Neither available (empty sequencer in Blender 5.1)
        else:
            strips = []

        for strip in strips:
            if hasattr(strip, "filepath") and strip.filepath:
                strip.filepath = sanitize_path(strip.filepath, placeholder)

    # Text blocks (Replace strings containing HOME_DIR)
    pattern = re.escape(HOME_DIR)
    for txt in bpy.data.texts:
        body = txt.as_string()
        if body and HOME_DIR in body:
            new_body = re.sub(pattern, placeholder, body)
            txt.clear()
            txt.write(new_body)


# ==============================
# Operator
# ==============================

class SANITIZEPATHS_OT_run(bpy.types.Operator):
    bl_idname = "system.sanitize_paths"
    bl_label = "Sanitize Paths"
    bl_description = "Normalize and anonymize file paths in the current .blend"

    def execute(self, context):
        non_packed_refs = find_non_packed_references()
        if non_packed_refs:
            preview = ", ".join(non_packed_refs[:3])
            if len(non_packed_refs) > 3:
                preview += ", ..."
            self.report(
                {'WARNING'},
                (
                    "Operation cancelled: non-packed external data was found. "
                    "Sanitizing paths would break references. "
                    f"Examples: {preview}"
                ),
            )
            return {'CANCELLED'}

        prefs = bpy.context.preferences.addons[__name__].preferences
        placeholder = prefs.home_placeholder

        sanitize_all_paths(placeholder)
        self.report({'INFO'}, f"Paths sanitized using placeholder: {placeholder}")
        return {'FINISHED'}


# ==============================
# Menu
# ==============================

def menu_func(self, context):
    self.layout.operator(SANITIZEPATHS_OT_run.bl_idname, icon='FILE_REFRESH')


# ==============================
# Register
# ==============================

classes = (
    SanitizePathsPreferences,
    SANITIZEPATHS_OT_run,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_external_data.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_external_data.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
