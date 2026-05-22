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


def sanitize_path(path: str, placeholder: str) -> str:
    """Normalize and anonymize paths containing user-specific information"""
    if not path:
        return path

    abs_path = bpy.path.abspath(path)

    # Home directory → Placeholder
    if abs_path.startswith(HOME_DIR):
        rel_from_home = os.path.relpath(abs_path, HOME_DIR)
        sanitized = os.path.join(placeholder, rel_from_home)
    else:
        sanitized = bpy.path.relpath(abs_path)

    return sanitized


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
        for strip in seq.sequences_all:
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
