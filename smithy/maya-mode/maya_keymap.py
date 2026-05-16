import bpy

def enable_maya_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if not kc:
        return

    km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')

    # Example: Alt + RMB = orbit (Maya-style)
    kmi = km.keymap_items.new('view3d.rotate', 'RIGHTMOUSE', 'PRESS', alt=True)
    kmi.active = True

def disable_maya_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    for km in kc.keymaps:
        if km.name == "3D View":
            kc.keymaps.remove(km)
            break
