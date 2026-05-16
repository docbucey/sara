import bpy
from .maya_keymap import enable_maya_keymap, disable_maya_keymap
from .maya_aliases import run_alias

class MAYA_OT_enable_mode(bpy.types.Operator):
    bl_idname = "maya_mode.enable"
    bl_label = "Enable Maya Mode"

    def execute(self, context):
        enable_maya_keymap()
        self.report({'INFO'}, "Maya Mode enabled.")
        return {'FINISHED'}


class MAYA_OT_disable_mode(bpy.types.Operator):
    bl_idname = "maya_mode.disable"
    bl_label = "Disable Maya Mode"

    def execute(self, context):
        disable_maya_keymap()
        self.report({'INFO'}, "Maya Mode disabled.")
        return {'FINISHED'}


class MAYA_OT_run_alias(bpy.types.Operator):
    bl_idname = "maya_mode.run_alias"
    bl_label = "Run Maya Alias"

    alias: bpy.props.StringProperty()

    def execute(self, context):
        run_alias(self.alias)
        return {'FINISHED'}
