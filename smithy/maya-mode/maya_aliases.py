import bpy

ALIASES = {
    "extrude": "mesh.extrude_region_move",
    "insert_edge_loop": "mesh.loopcut_slide",
    "isolate_select": "view3d.localview"
}

def run_alias(name: str):
    op = ALIASES.get(name)
    if not op:
        print(f"[MayaMode] Unknown alias: {name}")
        return
    bpy.ops.wm.call_menu(name=op)
