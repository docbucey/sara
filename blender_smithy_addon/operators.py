import os
import bpy
from .bridge import (
    smithy_handle_command, dispatch, dispatch_ai_request, check_health, is_sara_online,
    png_output_path, update_asset_meta, resolve_sara_root,
    xaml_output_path, update_asset_meta_xaml, format_drawing_brush, _rgba_to_wpf_hex,
)


class SMITHY_OT_ping(bpy.types.Operator):
    """Check if SARA CONTROL is reachable"""
    bl_idname = "smithy.ping"
    bl_label = "Smithy Ping"

    def execute(self, context):
        def _on_health(online, info):
            # bpy.app.timers runs on the main thread — safe to touch Blender data
            def _report():
                if online:
                    bpy.context.window_manager.sara_status = "ONLINE"
                else:
                    bpy.context.window_manager.sara_status = "OFFLINE"
            bpy.app.timers.register(_report, first_interval=0.0)

        check_health(callback=_on_health)
        self.report({'INFO'}, "SARA health check sent (check console).")
        return {'FINISHED'}


class SMITHY_OT_run_command(bpy.types.Operator):
    """Execute a command sent from Smithy"""
    bl_idname = "smithy.run_command"
    bl_label = "Smithy Run Command"

    command: bpy.props.StringProperty()

    def execute(self, context):
        smithy_handle_command(self.command)
        return {'FINISHED'}


class SMITHY_OT_dispatch(bpy.types.Operator):
    """Send the active file + task to SARA CONTROL for AI processing"""
    bl_idname = "smithy.dispatch"
    bl_label = "Send to SARA"
    bl_description = "Route the current task to SARA CONTROL (requires sara_control_http.py running)"

    task: bpy.props.StringProperty(name="Task", default="implement_logic")

    def execute(self, context):
        wm = context.window_manager
        file_path = bpy.data.filepath or "untitled.blend"
        task_desc = wm.sara_task if hasattr(wm, "sara_task") else self.task

        def _on_result(task_id, state, result):
            def _report():
                wm.sara_last_state = state
                wm.sara_last_result = str(result.get("result", result))
            bpy.app.timers.register(_report, first_interval=0.0)

        dispatch_ai_request(file_path, task_desc, callback=_on_result)
        self.report({'INFO'}, f"Dispatched to SARA: {task_desc}")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(self, "task", text="Task")


class SMITHY_PT_sara_panel(bpy.types.Panel):
    """SARA Bridge Panel in the Sidebar"""
    bl_label = "SARA Bridge"
    bl_idname = "SMITHY_PT_sara_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Smithy"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Status row
        status = getattr(wm, "sara_status", "UNKNOWN")
        row = layout.row()
        row.label(text=f"SARA: {status}",
                  icon="LINKED" if status == "ONLINE" else "UNLINKED")
        row.operator("smithy.ping", text="Check")

        layout.separator()

        # Task input + dispatch
        layout.prop(wm, "sara_task", text="Task")
        layout.operator("smithy.dispatch", text="Send to SARA", icon="PLAY")

        layout.separator()

        # Last result
        last_state = getattr(wm, "sara_last_state", "")
        if last_state:
            layout.label(text=f"Last state: {last_state}")
        last_result = getattr(wm, "sara_last_result", "")
        if last_result:
            box = layout.box()
            for line in last_result[:300].split("\n"):
                box.label(text=line)

        layout.separator()

        # --- Asset export section ---
        layout.label(text="Export Asset to SARA:", icon="EXPORT")
        layout.prop(wm, "sara_asset_id", text="Asset ID")

        layout.label(text="PNG (bitmap render):", icon="RENDER_STILL")
        row = layout.row(align=True)
        row.operator("smithy.render_to_sara", text="Render Scene", icon="RENDER_STILL")
        layout.operator("smithy.batch_render_collections", text="Batch: All Collections", icon="FILE_REFRESH")

        layout.label(text="XAML (code — zero file footprint):", icon="FILE_SCRIPT")
        layout.operator("smithy.export_to_xaml", text="Export Collection to XAML", icon="EXPORT")
        layout.label(text="Name objects sara_rx / sara_ry for corner radii.", icon="INFO")


class SMITHY_OT_render_to_sara(bpy.types.Operator):
    """Render current camera view to SARA assets/png/{asset_id}_4x3.png at 1024x768"""
    bl_idname = "smithy.render_to_sara"
    bl_label = "Render to SARA"
    bl_description = "Render the current scene to SARA assets/png/ (1024x768 PNG)"

    def _safe_id(self, raw: str) -> str:
        """Normalise to lowercase underscores, strip trailing _4x3 if typed."""
        s = raw.strip().lower().replace(" ", "_").replace("-", "_")
        if s.endswith("_4x3"):
            s = s[:-4]
        return s

    def execute(self, context):
        asset_id_raw = getattr(context.window_manager, "sara_asset_id", "").strip()
        if not asset_id_raw:
            self.report({'ERROR'}, "Enter an Asset ID in the panel first.")
            return {'CANCELLED'}

        base_id = self._safe_id(asset_id_raw)
        full_id = base_id + "_4x3"
        out_path = png_output_path(full_id)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        scene = context.scene
        orig = (
            scene.render.filepath,
            scene.render.image_settings.file_format,
            scene.render.resolution_x,
            scene.render.resolution_y,
            scene.render.resolution_percentage,
        )
        try:
            scene.render.resolution_x = 1024
            scene.render.resolution_y = 768
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = 'PNG'
            scene.render.filepath = out_path
            bpy.ops.render.render(write_still=True)
            update_asset_meta(full_id, 1024, 768)
            self.report({'INFO'}, f"Saved: {os.path.basename(out_path)}")
            context.window_manager.sara_last_result = f"Rendered → {out_path}"
        except Exception as e:
            self.report({'ERROR'}, f"Render failed: {e}")
            return {'CANCELLED'}
        finally:
            scene.render.filepath = orig[0]
            scene.render.image_settings.file_format = orig[1]
            scene.render.resolution_x = orig[2]
            scene.render.resolution_y = orig[3]
            scene.render.resolution_percentage = orig[4]
        return {'FINISHED'}


class SMITHY_OT_batch_render_collections(bpy.types.Operator):
    """
    Batch render every Blender collection whose name starts with 'sara_'
    to SARA assets/png/{collection_name}_4x3.png.
    Name your collections to match the asset IDs in assets_meta.json.
    """
    bl_idname = "smithy.batch_render_collections"
    bl_label = "Batch Render Collections"
    bl_description = (
        "Render each collection named sara_* to its matching SARA PNG.\n"
        "Name collections to match asset IDs (e.g. sara_hid_keyboard_qwerty_plate)"
    )

    def execute(self, context):
        scene = context.scene
        orig = (
            scene.render.filepath,
            scene.render.image_settings.file_format,
            scene.render.resolution_x,
            scene.render.resolution_y,
            scene.render.resolution_percentage,
        )
        rendered = 0
        errors = 0
        try:
            scene.render.resolution_x = 1024
            scene.render.resolution_y = 768
            scene.render.resolution_percentage = 100
            scene.render.image_settings.file_format = 'PNG'

            target_cols = [
                col for col in bpy.data.collections
                if col.name.lower().replace(" ", "_").replace("-", "_").startswith("sara_")
            ]

            if not target_cols:
                self.report({'WARNING'}, "No collections starting with 'sara_' found.")
                return {'CANCELLED'}

            # Hide all collections, render each sara_* one at a time
            all_cols = list(bpy.data.collections)
            for col in all_cols:
                col.hide_render = True

            for col in target_cols:
                col_id = col.name.lower().replace(" ", "_").replace("-", "_")
                if not col_id.endswith("_4x3"):
                    col_id = col_id + "_4x3"
                out_path = png_output_path(col_id)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                col.hide_render = False
                scene.render.filepath = out_path
                try:
                    bpy.ops.render.render(write_still=True)
                    update_asset_meta(col_id, 1024, 768)
                    rendered += 1
                    print(f"[Smithy] Rendered {col_id}")
                except Exception as e:
                    errors += 1
                    print(f"[Smithy] Failed {col_id}: {e}")
                finally:
                    col.hide_render = True

            # Restore all visible
            for col in all_cols:
                col.hide_render = False

            self.report({'INFO'}, f"Batch done: {rendered} rendered, {errors} errors.")
            context.window_manager.sara_last_result = (
                f"Batch: {rendered} rendered, {errors} errors → assets/png/"
            )
        except Exception as e:
            self.report({'ERROR'}, f"Batch failed: {e}")
            return {'CANCELLED'}
        finally:
            scene.render.filepath = orig[0]
            scene.render.image_settings.file_format = orig[1]
            scene.render.resolution_x = orig[2]
            scene.render.resolution_y = orig[3]
            scene.render.resolution_percentage = orig[4]
        return {'FINISHED'}


class SMITHY_OT_export_to_xaml(bpy.types.Operator):
    """
    Read the active (or named) Blender collection and export it as WPF
    DrawingBrush XAML — zero binary assets, zero PNG, pure code.

    Workflow:
      1. Build your UI element as a collection of mesh objects in Blender.
      2. Name the collection to match the SARA asset ID
         (e.g.  sara_office_btn_primary  — _4x3 appended automatically).
      3. Set each object's material diffuse color to the color you want.
      4. Optional: add a custom property  sara_rx  (float) for corner radius.
      5. Click Export — XAML lands in  assets/xaml/{id}.xaml  and
         assets_meta.json is updated with  procedural_xaml_ref.

    Object Z position controls draw order (higher Z = drawn on top).
    The C# app merges the ResourceDictionary; falls back to PNG if absent.
    """
    bl_idname = "smithy.export_to_xaml"
    bl_label = "Export Collection to XAML"
    bl_description = (
        "Export active collection as WPF DrawingBrush XAML.\n"
        "No PNG rendered — the XAML IS the asset."
    )

    def _safe_id(self, raw: str) -> str:
        s = raw.strip().lower().replace(" ", "_").replace("-", "_")
        if s.endswith("_4x3"):
            s = s[:-4]
        return s

    def _collection_bounds(self, col):
        """Return (min_x, min_y, max_x, max_y) of all mesh objects in world space."""
        from mathutils import Vector
        xs, ys = [], []
        for obj in col.objects:
            if obj.type not in ('MESH', 'CURVE', 'FONT', 'SURFACE'):
                continue
            for corner in obj.bound_box:
                wc = obj.matrix_world @ Vector(corner)
                xs.append(wc.x)
                ys.append(wc.y)
        if not xs:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def _obj_to_element(self, obj, cx_min, cy_min, cx_size, cy_size) -> dict:
        """Convert one Blender object to a normalized drawing element dict."""
        from mathutils import Vector
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        xs = [c.x for c in corners]
        ys = [c.y for c in corners]
        x = (min(xs) - cx_min) / cx_size
        y = 1.0 - (max(ys) - cy_min) / cy_size   # flip Y: Blender up → WPF down
        w = (max(xs) - min(xs)) / cx_size
        h = (max(ys) - min(ys)) / cy_size

        # Material color
        color = "#CCCCCC"
        if obj.active_material and hasattr(obj.active_material, "diffuse_color"):
            color = _rgba_to_wpf_hex(obj.active_material.diffuse_color)

        # Custom corner radius — add a float custom prop named sara_rx on the object
        rx = float(obj.get("sara_rx", 0.0))
        ry = float(obj.get("sara_ry", rx))

        return {
            "color": color,
            "x": round(x, 5), "y": round(y, 5),
            "w": round(max(w, 0.001), 5), "h": round(max(h, 0.001), 5),
            "rx": round(rx, 5), "ry": round(ry, 5),
            "label": obj.name,
        }

    def execute(self, context):
        wm = context.window_manager
        asset_id_raw = getattr(wm, "sara_asset_id", "").strip()

        # Resolve which collection to export
        col = None
        if asset_id_raw:
            base = self._safe_id(asset_id_raw)
            full_id = base + "_4x3"
            # Try exact name match first, then base name
            for candidate in (full_id, base, asset_id_raw.strip()):
                col = bpy.data.collections.get(candidate)
                if col:
                    break
        if col is None:
            # Fall back to active object's collection
            obj = context.active_object
            if obj and obj.users_collection:
                col = obj.users_collection[0]
        if col is None:
            self.report({'ERROR'}, "No collection found. Enter Asset ID or select an object.")
            return {'CANCELLED'}

        # Derive final asset_id from collection name if not set
        if not asset_id_raw:
            full_id = col.name.lower().replace(" ", "_").replace("-", "_")
            if not full_id.endswith("_4x3"):
                full_id += "_4x3"
        else:
            full_id = self._safe_id(asset_id_raw) + "_4x3"

        # Get canvas bounds
        bounds = self._collection_bounds(col)
        if bounds is None:
            self.report({'ERROR'}, f"Collection '{col.name}' has no mesh objects.")
            return {'CANCELLED'}
        cx_min, cy_min, cx_max, cy_max = bounds
        cx_size = max(cx_max - cx_min, 0.0001)
        cy_size = max(cy_max - cy_min, 0.0001)

        # Convert objects → elements, sorted by Z (background first)
        drawable = [
            o for o in col.objects
            if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE')
        ]
        drawable.sort(key=lambda o: o.location.z)
        elements = [self._obj_to_element(o, cx_min, cy_min, cx_size, cy_size)
                    for o in drawable]

        if not elements:
            self.report({'ERROR'}, "No drawable objects found in collection.")
            return {'CANCELLED'}

        # Format and save XAML
        xaml_str = format_drawing_brush(full_id, elements)
        out_path = xaml_output_path(full_id)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(xaml_str)
        except Exception as e:
            self.report({'ERROR'}, f"Could not write XAML: {e}")
            return {'CANCELLED'}

        # Update meta
        update_asset_meta_xaml(full_id, full_id)

        self.report({'INFO'}, f"Exported {len(elements)} objects → {os.path.basename(out_path)}")
        wm.sara_last_result = f"XAML → assets/xaml/{full_id}.xaml  ({len(elements)} elements)"
        return {'FINISHED'}

