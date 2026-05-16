bl_info = {
    "name": "Smithy Bridge",
    "author": "MD",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Smithy",
    "description": "Smithy ↔ SARA CONTROL Bridge for Blender",
    "category": "System",
}

import bpy
from .operators import (
    SMITHY_OT_ping,
    SMITHY_OT_run_command,
    SMITHY_OT_dispatch,
    SMITHY_OT_render_to_sara,
    SMITHY_OT_batch_render_collections,
    SMITHY_OT_export_to_xaml,
    SMITHY_PT_sara_panel,
)
from .bridge import check_health

classes = (
    SMITHY_OT_ping,
    SMITHY_OT_run_command,
    SMITHY_OT_dispatch,
    SMITHY_OT_render_to_sara,
    SMITHY_OT_batch_render_collections,
    SMITHY_OT_export_to_xaml,
    SMITHY_PT_sara_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # WindowManager properties for panel state
    bpy.types.WindowManager.sara_status = bpy.props.StringProperty(
        name="SARA Status", default="UNKNOWN"
    )
    bpy.types.WindowManager.sara_task = bpy.props.StringProperty(
        name="Task", default="implement_logic"
    )
    bpy.types.WindowManager.sara_last_state = bpy.props.StringProperty(
        name="Last State", default=""
    )
    bpy.types.WindowManager.sara_last_result = bpy.props.StringProperty(
        name="Last Result", default=""
    )
    bpy.types.WindowManager.sara_asset_id = bpy.props.StringProperty(
        name="Asset ID",
        description="SARA asset ID to render to (e.g. sara_hid_keyboard_qwerty_plate). _4x3 is appended automatically.",
        default=""
    )

    # Non-blocking health check on addon load
    check_health()
    print("Smithy Bridge: SARA CONTROL bridge loaded.")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.sara_status
    del bpy.types.WindowManager.sara_task
    del bpy.types.WindowManager.sara_last_state
    del bpy.types.WindowManager.sara_last_result
    del bpy.types.WindowManager.sara_asset_id

