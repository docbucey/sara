#!/usr/bin/env python3
"""
One-shot SARA asset bootstrap (no Ollama):
  - Multi-threaded procedural PNG generation (1024×768, 4:3 cartoon placeholders)
  - assets/meta/assets_meta.json + assets/meta/sara_themes.json
  - ICO from your desktop master PNG (last step)

Edit DESKTOP_PNG_FOR_ICO if your path moves. Requires: pip install pillow

  python tools/sara_bootstrap_assets.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Paths (change if needed)
# ---------------------------------------------------------------------------
_DESKTOP_DEFAULT = r"C:\Users\mdbuc\OneDrive\Desktop\sarabackground.png"
SARA_ROOT = Path(__file__).resolve().parents[1]
OUT_PNG_DIR = SARA_ROOT / "assets" / "png"
OUT_META_DIR = SARA_ROOT / "assets" / "meta"
OUT_ICO_DIR = SARA_ROOT / "assets" / "ico"
DESKTOP_PNG_FOR_ICO = Path(os.environ.get("SARA_DESKTOP_PNG", _DESKTOP_DEFAULT))
ICO_OUT = OUT_ICO_DIR / "sara.ico"

W, H = 1024, 768

# Every PNG filename you listed (including items marked opt in your note).
ASSET_FILENAMES: List[str] = [
    # Shared office / cookie-cutter chrome
    "sara_office_panel_bg_main_4x3.png",
    "sara_office_panel_bg_dialog_4x3.png",
    "sara_office_titlebar_tile_4x3.png",
    "sara_office_btn_primary_4x3.png",
    "sara_office_btn_secondary_4x3.png",
    "sara_office_btn_icon_square_4x3.png",
    "sara_office_btn_close_4x3.png",
    "sara_office_btn_minimize_4x3.png",
    "sara_office_btn_maximize_4x3.png",
    "sara_office_scroll_track_v_4x3.png",
    "sara_office_scroll_thumb_v_4x3.png",
    "sara_office_scroll_track_h_4x3.png",
    "sara_office_scroll_thumb_h_4x3.png",
    "sara_office_input_field_4x3.png",
    "sara_office_list_row_4x3.png",
    "sara_office_tab_inactive_4x3.png",
    "sara_office_tab_active_4x3.png",
    "sara_office_separator_h_4x3.png",
    "sara_office_separator_v_4x3.png",
    "sara_office_tooltip_bubble_4x3.png",
    "sara_office_menubar_strip_4x3.png",
    # Fatigue / status
    "sara_status_fatigue_meter_frame_4x3.png",
    "sara_status_fatigue_meter_fill_green_4x3.png",
    "sara_status_fatigue_meter_fill_yellow_4x3.png",
    "sara_status_fatigue_meter_fill_red_4x3.png",
    "sara_status_icon_energy_4x3.png",
    "sara_status_icon_stress_4x3.png",
    "sara_status_icon_sleep_4x3.png",
    "sara_status_toast_banner_4x3.png",
    # Launcher + app icons
    "sara_launcher_bg_desktop_4x3.png",
    "sara_launcher_taskbar_tile_4x3.png",
    "sara_icon_app_geek_4x3.png",
    "sara_icon_app_secretary_4x3.png",
    "sara_icon_app_marketing_4x3.png",
    "sara_icon_app_accountant_4x3.png",
    "sara_icon_app_settings_mapper_4x3.png",
    "sara_icon_app_phone_4x3.png",
    # Secretary / Marketing / Accountant
    "sara_secretary_panel_bg_4x3.png",
    "sara_secretary_inbox_list_chrome_4x3.png",
    "sara_secretary_calendar_chrome_4x3.png",
    "sara_marketing_panel_bg_4x3.png",
    "sara_marketing_campaign_board_chrome_4x3.png",
    "sara_accountant_panel_bg_4x3.png",
    "sara_accountant_ledger_chrome_4x3.png",
    # Geek + football / calibration
    "sara_geek_panel_bg_4x3.png",
    "sara_geek_terminal_window_chrome_4x3.png",
    "sara_football_field_bg_4x3.png",
    "sara_football_endzone_stripes_4x3.png",
    "sara_football_target_ring_4x3.png",
    "sara_football_ball_4x3.png",
    # DisabilityMapper shell
    "sara_mapper_shell_bg_4x3.png",
    "sara_mapper_shell_sidebar_chrome_4x3.png",
    "sara_mapper_shell_device_slot_4x3.png",
    "sara_mapper_shell_profile_bar_4x3.png",
    "sara_mapper_shell_mapping_canvas_4x3.png",
    # HID — joystick
    "sara_hid_joystick_base_4x3.png",
    "sara_hid_joystick_cap_only_4x3.png",
    "sara_hid_throttle_quadrant_4x3.png",
    "sara_hid_hat_switch_diagram_4x3.png",
    # HID — macro pad
    "sara_hid_macro_grid_plate_empty_4x3.png",
    "sara_hid_macro_grid_example_filled_4x3.png",
    "sara_hid_macro_keycap_single_4x3.png",
    "sara_hid_macro_bezel_streamdeck_like_4x3.png",
    # HID — steno
    "sara_hid_steno_machine_silhouette_4x3.png",
    "sara_hid_steno_key_well_left_4x3.png",
    "sara_hid_steno_key_well_right_4x3.png",
    "sara_hid_steno_number_bar_4x3.png",
    "sara_hid_steno_thumb_cluster_4x3.png",
    # Virtual keyboards
    "sara_hid_keyboard_qwerty_plate_4x3.png",
    "sara_hid_keyboard_compact_plate_4x3.png",
    "sara_hid_keyboard_numeric_plate_4x3.png",
    "sara_hid_keyboard_symbols_plate_4x3.png",
    "sara_hid_keyboard_qwerty_painted_lowercase_4x3.png",
    "sara_hid_keyboard_symbols_painted_4x3.png",
    "sara_hid_keycap_blank_round_4x3.png",
    "sara_hid_keycap_blank_square_4x3.png",
]

_lock = threading.Lock()
_errors: List[str] = []


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.strip().lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


@dataclass(frozen=True)
class ThemeColors:
    surface: Tuple[int, int, int, int]
    surface_menu: Tuple[int, int, int, int]
    accent: Tuple[int, int, int, int]
    accent2: Tuple[int, int, int, int]
    outline: Tuple[int, int, int, int]
    field: Tuple[int, int, int, int]
    text_muted: Tuple[int, int, int, int]


THEMES: Dict[str, ThemeColors] = {
    "popcap_default": ThemeColors(
        surface=(*_hex_to_rgb("#F4F6FA"), 255),
        surface_menu=(*_hex_to_rgb("#EEF1F7"), 255),
        accent=(*_hex_to_rgb("#2F6FED"), 255),
        accent2=(*_hex_to_rgb("#6BCB59"), 255),
        outline=(*_hex_to_rgb("#1B2433"), 255),
        field=(*_hex_to_rgb("#6BCB59"), 255),
        text_muted=(*_hex_to_rgb("#4B5A73"), 255),
    ),
    # Murray State University — blue / gold (no logos; palette only)
    "murray_state_racers": ThemeColors(
        surface=(*_hex_to_rgb("#002144"), 255),
        surface_menu=(*_hex_to_rgb("#003366"), 255),
        accent=(*_hex_to_rgb("#FFD100"), 255),
        accent2=(*_hex_to_rgb("#FFFFFF"), 255),
        outline=(*_hex_to_rgb("#FFD100"), 255),
        field=(*_hex_to_rgb("#1a4d2e"), 255),
        text_muted=(*_hex_to_rgb("#CCE0FF"), 255),
    ),
    # SEC-inspired accents (colors only — no marks)
    "sec_alabama": ThemeColors(
        surface=(*_hex_to_rgb("#FFF5F5"), 255),
        surface_menu=(*_hex_to_rgb("#FAD4D4"), 255),
        accent=(*_hex_to_rgb("#9E1B32"), 255),
        accent2=(*_hex_to_rgb("#828A8F"), 255),
        outline=(*_hex_to_rgb("#1B2433"), 255),
        field=(*_hex_to_rgb("#5C8F4F"), 255),
        text_muted=(*_hex_to_rgb("#4B5A73"), 255),
    ),
    "sec_auburn": ThemeColors(
        surface=(*_hex_to_rgb("#F7F4ED"), 255),
        surface_menu=(*_hex_to_rgb("#EDE6D6"), 255),
        accent=(*_hex_to_rgb("#0C2340"), 255),
        accent2=(*_hex_to_rgb("#E87722"), 255),
        outline=(*_hex_to_rgb("#0C2340"), 255),
        field=(*_hex_to_rgb("#6B9E4E"), 255),
        text_muted=(*_hex_to_rgb("#3D4F66"), 255),
    ),
    "sec_florida": ThemeColors(
        surface=(*_hex_to_rgb("#F2F8FF"), 255),
        surface_menu=(*_hex_to_rgb("#D9E8FA"), 255),
        accent=(*_hex_to_rgb("#0021A5"), 255),
        accent2=(*_hex_to_rgb("#FA4616"), 255),
        outline=(*_hex_to_rgb("#0021A5"), 255),
        field=(*_hex_to_rgb("#5FAF6A"), 255),
        text_muted=(*_hex_to_rgb("#2E4A73"), 255),
    ),
    "sec_georgia": ThemeColors(
        surface=(*_hex_to_rgb("#F9F9F9"), 255),
        surface_menu=(*_hex_to_rgb("#EDEDED"), 255),
        accent=(*_hex_to_rgb("#BA0C2F"), 255),
        accent2=(*_hex_to_rgb("#000000"), 255),
        outline=(*_hex_to_rgb("#000000"), 255),
        field=(*_hex_to_rgb("#5E8F4F"), 255),
        text_muted=(*_hex_to_rgb("#444444"), 255),
    ),
    "sec_kentucky": ThemeColors(
        surface=(*_hex_to_rgb("#F4F6FA"), 255),
        surface_menu=(*_hex_to_rgb("#E3E8F0"), 255),
        accent=(*_hex_to_rgb("#0033A0"), 255),
        accent2=(*_hex_to_rgb("#FFFFFF"), 255),
        outline=(*_hex_to_rgb("#0033A0"), 255),
        field=(*_hex_to_rgb("#6BA368"), 255),
        text_muted=(*_hex_to_rgb("#334466"), 255),
    ),
    "sec_lsu": ThemeColors(
        surface=(*_hex_to_rgb("#FDF8E7"), 255),
        surface_menu=(*_hex_to_rgb("#F5E6B3"), 255),
        accent=(*_hex_to_rgb("#461D7C"), 255),
        accent2=(*_hex_to_rgb("#FDD023"), 255),
        outline=(*_hex_to_rgb("#461D7C"), 255),
        field=(*_hex_to_rgb("#5C8F4F"), 255),
        text_muted=(*_hex_to_rgb("#4A3B66"), 255),
    ),
    "sec_tennessee": ThemeColors(
        surface=(*_hex_to_rgb("#F4F6FA"), 255),
        surface_menu=(*_hex_to_rgb("#E8EEF7"), 255),
        accent=(*_hex_to_rgb("#FF8200"), 255),
        accent2=(*_hex_to_rgb("#FFFFFF"), 255),
        outline=(*_hex_to_rgb("#58595B"), 255),
        field=(*_hex_to_rgb("#5FA06F"), 255),
        text_muted=(*_hex_to_rgb("#3D4F5C"), 255),
    ),
    "sec_texas_am": ThemeColors(
        surface=(*_hex_to_rgb("#FFF8F0"), 255),
        surface_menu=(*_hex_to_rgb("#FFE8D2"), 255),
        accent=(*_hex_to_rgb("#500000"), 255),
        accent2=(*_hex_to_rgb("#FFFFFF"), 255),
        outline=(*_hex_to_rgb("#500000"), 255),
        field=(*_hex_to_rgb("#6B8E4F"), 255),
        text_muted=(*_hex_to_rgb("#5C4033"), 255),
    ),
    "sec_arkansas": ThemeColors(
        surface=(*_hex_to_rgb("#F7F7F7"), 255),
        surface_menu=(*_hex_to_rgb("#E8E8E8"), 255),
        accent=(*_hex_to_rgb("#9D2235"), 255),
        accent2=(*_hex_to_rgb("#FFFFFF"), 255),
        outline=(*_hex_to_rgb("#1B2433"), 255),
        field=(*_hex_to_rgb("#5F9A55"), 255),
        text_muted=(*_hex_to_rgb("#444444"), 255),
    ),
    "sec_mississippi_state": ThemeColors(
        surface=(*_hex_to_rgb("#F4F6FA"), 255),
        surface_menu=(*_hex_to_rgb("#E0E6ED"), 255),
        accent=(*_hex_to_rgb("#660000"), 255),
        accent2=(*_hex_to_rgb("#FFFFFF"), 255),
        outline=(*_hex_to_rgb("#1B2433"), 255),
        field=(*_hex_to_rgb("#6B9E5E"), 255),
        text_muted=(*_hex_to_rgb("#3A3A3A"), 255),
    ),
    "sec_mississippi": ThemeColors(
        surface=(*_hex_to_rgb("#F2F6FB"), 255),
        surface_menu=(*_hex_to_rgb("#DCE6F3"), 255),
        accent=(*_hex_to_rgb("#14213D"), 255),
        accent2=(*_hex_to_rgb("#CE1126"), 255),
        outline=(*_hex_to_rgb("#14213D"), 255),
        field=(*_hex_to_rgb("#5FAF70"), 255),
        text_muted=(*_hex_to_rgb("#2E3D55"), 255),
    ),
    "sec_missouri": ThemeColors(
        surface=(*_hex_to_rgb("#F4F4F4"), 255),
        surface_menu=(*_hex_to_rgb("#E0E0E0"), 255),
        accent=(*_hex_to_rgb("#F1B82D"), 255),
        accent2=(*_hex_to_rgb("#000000"), 255),
        outline=(*_hex_to_rgb("#000000"), 255),
        field=(*_hex_to_rgb("#6B9E55"), 255),
        text_muted=(*_hex_to_rgb("#333333"), 255),
    ),
    "sec_oklahoma": ThemeColors(
        surface=(*_hex_to_rgb("#FFFDF8"), 255),
        surface_menu=(*_hex_to_rgb("#F5EFE3"), 255),
        accent=(*_hex_to_rgb("#841617"), 255),
        accent2=(*_hex_to_rgb("#DFD7C3"), 255),
        outline=(*_hex_to_rgb("#1B2433"), 255),
        field=(*_hex_to_rgb("#6B8F55"), 255),
        text_muted=(*_hex_to_rgb("#4A3C3C"), 255),
    ),
    "sec_south_carolina": ThemeColors(
        surface=(*_hex_to_rgb("#F9F9F9"), 255),
        surface_menu=(*_hex_to_rgb("#EDEDED"), 255),
        accent=(*_hex_to_rgb("#73000A"), 255),
        accent2=(*_hex_to_rgb("#000000"), 255),
        outline=(*_hex_to_rgb("#000000"), 255),
        field=(*_hex_to_rgb("#5FAF6A"), 255),
        text_muted=(*_hex_to_rgb("#444444"), 255),
    ),
    "sec_vanderbilt": ThemeColors(
        surface=(*_hex_to_rgb("#F4F6FA"), 255),
        surface_menu=(*_hex_to_rgb("#E4E9F2"), 255),
        accent=(*_hex_to_rgb("#866D4B"), 255),
        accent2=(*_hex_to_rgb("#000000"), 255),
        outline=(*_hex_to_rgb("#000000"), 255),
        field=(*_hex_to_rgb("#6BAF5F"), 255),
        text_muted=(*_hex_to_rgb("#3D4F66"), 255),
    ),
}


def _rr(draw, xy: Tuple[int, int, int, int], fill, outline, width: int = 3, radius: int = 12) -> None:
    """Rounded rect using circles at corners + rects (no PIL rounded_rectangle dependency)."""
    x0, y0, x1, y1 = xy
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    r = min(radius, (x1 - x0) // 2, (y1 - y0) // 2)
    if r < 4:
        draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)
        return
    # center rects
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill, outline=None)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill, outline=None)
    # corners
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=None)
    # outline path: draw thick stroke as rounded frame
    draw.rectangle([x0, y0, x1, y1], outline=outline, width=width)


def _label(draw, text: str, t: ThemeColors, y: int = 720) -> None:
    try:
        from PIL import ImageFont

        font = ImageFont.load_default()
    except Exception:
        return
    draw.text((16, y), text[:80], fill=t.outline, font=font)


def _draw_office(name: str, t: ThemeColors, draw, im) -> None:
    white = (255, 255, 255, 255)
    _rr(draw, (24, 24, W - 24, H - 24), t.surface, t.outline, 4, 16)
    if "titlebar" in name or "menubar" in name:
        _rr(draw, (40, 28, W - 40, 90), t.surface_menu, t.outline, 3, 10)
    if "btn_primary" in name:
        _rr(draw, (W // 2 - 160, H // 2 - 40, W // 2 + 160, H // 2 + 40), t.accent, t.outline, 4, 18)
    elif "btn_secondary" in name:
        _rr(draw, (W // 2 - 160, H // 2 - 40, W // 2 + 160, H // 2 + 40), t.surface_menu, t.outline, 4, 18)
    elif "btn_close" in name or "btn_minimize" in name or "btn_maximize" in name or "btn_icon" in name:
        s = 120
        _rr(draw, (W // 2 - s // 2, H // 2 - s // 2, W // 2 + s // 2, H // 2 + s // 2), t.accent2, t.outline, 4, 20)
    elif "scroll_track_v" in name:
        _rr(draw, (W // 2 - 24, 80, W // 2 + 24, H - 80), t.surface_menu, t.outline, 3, 8)
    elif "scroll_thumb_v" in name:
        _rr(draw, (W // 2 - 20, H // 2 - 120, W // 2 + 20, H // 2 + 120), t.accent, t.outline, 3, 10)
    elif "scroll_track_h" in name:
        _rr(draw, (80, H // 2 - 24, W - 80, H // 2 + 24), t.surface_menu, t.outline, 3, 8)
    elif "scroll_thumb_h" in name:
        _rr(draw, (W // 2 - 160, H // 2 - 18, W // 2 + 160, H // 2 + 18), t.accent, t.outline, 3, 10)
    elif "input_field" in name:
        _rr(draw, (80, H // 2 - 36, W - 80, H // 2 + 36), white, t.outline, 3, 10)
    elif "list_row" in name:
        for i, y0 in enumerate(range(120, 620, 56)):
            _rr(draw, (60, y0, W - 60, y0 + 48), t.surface_menu if i % 2 == 0 else t.surface, t.outline, 2, 8)
    elif "tab_inactive" in name:
        _rr(draw, (60, 60, 220, 120), t.surface_menu, t.outline, 2, 10)
    elif "tab_active" in name:
        _rr(draw, (60, 60, 240, 130), t.accent, t.outline, 3, 12)
    elif "separator_h" in name:
        draw.rectangle([60, H // 2 - 3, W - 60, H // 2 + 3], fill=t.outline)
    elif "separator_v" in name:
        draw.rectangle([W // 2 - 3, 80, W // 2 + 3, H - 80], fill=t.outline)
    elif "tooltip" in name:
        _rr(draw, (W // 2 - 200, H // 2 - 60, W // 2 + 200, H // 2 + 60), (255, 255, 230, 255), t.outline, 3, 16)
    elif "dialog" in name:
        _rr(draw, (120, 120, W - 120, H - 120), white, t.outline, 4, 14)
    else:
        inner = (80, 100, W - 80, H - 80)
        _rr(draw, inner, white, t.outline, 3, 14)


def _icon_letter(name: str) -> str:
    if "geek" in name:
        return "G"
    if "secretary" in name:
        return "S"
    if "marketing" in name:
        return "M"
    if "accountant" in name:
        return "A"
    if "settings" in name or "mapper" in name:
        return "K"
    if "phone" in name:
        return "P"
    return "?"


def _draw_icon_app(name: str, t: ThemeColors, draw, im) -> None:
    cx, cy, r = W // 2, H // 2, 220
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=t.accent, outline=t.outline, width=6)
    ch = _icon_letter(name)
    # big letter
    try:
        from PIL import ImageFont

        font = ImageFont.truetype("segoeui.ttf", 200)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), ch, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 10), ch, fill=t.accent2, font=font)


def _draw_status(name: str, t: ThemeColors, draw, im) -> None:
    if "frame" in name:
        _rr(draw, (120, 280, W - 120, 420), t.surface_menu, t.outline, 4, 16)
    elif "fill_green" in name:
        draw.rectangle([140, 300, W - 140, 400], fill=(80, 200, 100, 255), outline=t.outline, width=3)
    elif "fill_yellow" in name:
        draw.rectangle([140, 300, W - 140, 400], fill=(240, 210, 80, 255), outline=t.outline, width=3)
    elif "fill_red" in name:
        draw.rectangle([140, 300, W - 140, 400], fill=(220, 70, 70, 255), outline=t.outline, width=3)
    elif "icon_energy" in name:
        draw.polygon([(W // 2, 120), (W // 2 + 140, H - 120), (W // 2 - 140, H - 120)], fill=t.accent2, outline=t.outline, width=4)
    elif "icon_stress" in name:
        for i in range(5):
            x0 = 200 + i * 90
            draw.rectangle([x0, H // 2 - 80, x0 + 50, H // 2 + 80], fill=t.accent, outline=t.outline, width=3)
    elif "icon_sleep" in name:
        draw.arc([W // 2 - 180, H // 2 - 120, W // 2 + 180, H // 2 + 120], 200, 340, fill=t.outline, width=10)
    elif "toast" in name:
        _rr(draw, (80, H // 2 - 70, W - 80, H // 2 + 70), t.accent2, t.outline, 4, 20)
    else:
        _rr(draw, (40, 40, W - 40, H - 40), t.surface, t.outline, 3, 12)


def _draw_launcher(name: str, t: ThemeColors, draw, im) -> None:
    if "launcher_bg" in name:
        for i in range(8):
            y = 60 + i * 86
            _rr(draw, (60, y, W - 60, y + 72), t.surface_menu if i % 2 == 0 else t.surface, t.outline, 2, 14)
    else:
        _rr(draw, (W // 2 - 200, H // 2 - 80, W // 2 + 200, H // 2 + 80), t.surface_menu, t.outline, 3, 16)


def _draw_app_panel(name: str, t: ThemeColors, draw, im) -> None:
    _rr(draw, (32, 32, W - 32, H - 32), t.surface, t.outline, 4, 14)
    if "inbox" in name or "list" in name:
        for y in range(140, 640, 50):
            _rr(draw, (80, y, W - 80, y + 40), (255, 255, 255, 255), t.outline, 2, 8)
    elif "calendar" in name:
        cell = 80
        for row in range(5):
            for col in range(7):
                x0, y0 = 100 + col * cell, 140 + row * cell
                _rr(draw, (x0 + 4, y0 + 4, x0 + cell - 4, y0 + cell - 4), t.surface_menu, t.outline, 1, 6)
    elif "campaign" in name or "board" in name:
        for i in range(6):
            _rr(draw, (80 + i * 140, 200, 200 + i * 140, 520), t.surface_menu, t.outline, 2, 12)
    elif "ledger" in name:
        for y in range(160, 680, 36):
            draw.line([(100, y), (W - 100, y)], fill=t.outline, width=2)
    else:
        _rr(draw, (100, 140, W - 100, H - 100), (255, 255, 255, 255), t.outline, 2, 10)


def _draw_geek_football(name: str, t: ThemeColors, draw, im) -> None:
    if "football_field" in name or "field_bg" in name:
        _rr(draw, (20, 20, W - 20, H - 20), t.field, t.outline, 4, 8)
        draw.line([(W // 2, 40), (W // 2, H - 40)], fill=(255, 255, 255, 255), width=6)
        draw.line([(40, H // 2), (W - 40, H // 2)], fill=(255, 255, 255, 255), width=4)
    elif "endzone" in name:
        draw.rectangle([40, 40, W - 40, 200], fill=(255, 255, 255, 40), outline=t.outline, width=3)
        for x in range(80, W - 80, 50):
            draw.line([(x, 40), (x, 200)], fill=t.outline, width=3)
    elif "target_ring" in name:
        cx, cy, r = W // 2, H // 2, 200
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=t.outline, width=8)
        draw.ellipse([cx - r + 40, cy - r + 40, cx + r - 40, cy + r - 40], outline=t.accent2, width=6)
    elif "football_ball" in name:
        cx, cy, r = W // 2, H // 2, 140
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 240, 220, 255), outline=t.outline, width=5)
        draw.arc([cx - r, cy - r, cx + r, cy + r], 30, 120, fill=t.outline, width=6)
    elif "terminal" in name:
        _rr(draw, (60, 60, W - 60, H - 60), (20, 24, 32, 255), t.outline, 3, 8)
        for i, y in enumerate(range(120, 620, 36)):
            draw.rectangle([90, y, W - 120, y + 24], fill=(60, 180, 90, 255) if i % 3 == 0 else (80, 80, 120, 255))
    else:
        _rr(draw, (40, 40, W - 40, H - 40), t.surface, t.outline, 3, 12)


def _draw_mapper(name: str, t: ThemeColors, draw, im) -> None:
    _rr(draw, (16, 16, W - 16, H - 16), t.surface, t.outline, 3, 10)
    if "sidebar" in name:
        _rr(draw, (32, 32, 220, H - 32), t.surface_menu, t.outline, 3, 10)
    elif "device_slot" in name:
        _rr(draw, (W // 2 - 200, 120, W // 2 + 200, 360), (255, 255, 255, 255), t.outline, 4, 16)
    elif "profile_bar" in name:
        _rr(draw, (240, 32, W - 32, 100), t.surface_menu, t.outline, 3, 8)
    elif "mapping_canvas" in name:
        _rr(draw, (240, 120, W - 32, H - 32), (255, 255, 255, 255), t.outline, 3, 10)
    else:
        _rr(draw, (240, 120, W - 32, H - 32), (255, 255, 255, 255), t.outline, 2, 8)


def _draw_joystick(name: str, t: ThemeColors, draw, im) -> None:
    n = name.lower()
    if "cap_only" in n:
        draw.rectangle([0, 0, W, H], fill=(0, 0, 0, 0))
        cx, cy, r = W // 2, H // 2, 140
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=t.accent2, outline=t.outline, width=6)
        return
    if "throttle" in n:
        for i in range(3):
            x = 200 + i * 200
            _rr(draw, (x - 40, H // 2 - 200, x + 40, H // 2 + 200), t.surface_menu, t.outline, 3, 12)
        return
    if "hat" in n:
        cx, cy = W // 2, H // 2
        arm = 100
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            x1, y1 = cx + dx * arm, cy + dy * arm
            draw.line([(cx, cy), (x1, y1)], fill=t.outline, width=8)
            draw.ellipse([x1 - 20, y1 - 20, x1 + 20, y1 + 20], fill=t.accent, outline=t.outline, width=3)
        return
    draw.ellipse([W // 2 - 280, H // 2 + 80, W // 2 + 280, H // 2 + 320], fill=t.surface_menu, outline=t.outline, width=5)
    _rr(draw, (W // 2 - 90, H // 2 - 200, W // 2 + 90, H // 2 + 120), t.surface_menu, t.outline, 4, 24)
    draw.ellipse([W // 2 - 100, H // 2 - 280, W // 2 + 100, H // 2 - 80], fill=t.accent2, outline=t.outline, width=5)


def _draw_macro(name: str, t: ThemeColors, draw, im) -> None:
    rows, cols = (3, 5)
    if "keycap_single" in name:
        _rr(draw, (W // 2 - 80, H // 2 - 80, W // 2 + 80, H // 2 + 80), (255, 255, 255, 255), t.outline, 4, 16)
        return
    if "bezel" in name:
        _rr(draw, (40, 80, W - 40, H - 40), t.surface_menu, t.outline, 5, 20)
        return
    margin_x, margin_y = 80, 100
    cw = (W - 2 * margin_x) // cols
    ch = (H - 2 * margin_y) // rows
    for r in range(rows):
        for c in range(cols):
            x0 = margin_x + c * cw + 6
            y0 = margin_y + r * ch + 6
            fill = t.accent if ("example_filled" in name and (r + c) % 3 == 0) else (255, 255, 255, 255)
            _rr(draw, (x0, y0, x0 + cw - 12, y0 + ch - 12), fill, t.outline, 2, 10)


def _draw_steno(name: str, t: ThemeColors, draw, im) -> None:
    if "silhouette" in name:
        _rr(draw, (W // 2 - 380, 80, W // 2 + 380, H - 60), t.surface_menu, t.outline, 4, 20)
        return
    if "number_bar" in name:
        for i, x in enumerate(range(100, W - 100, 90)):
            _rr(draw, (x, H // 2 - 40, x + 70, H // 2 + 40), (255, 255, 255, 255), t.outline, 2, 8)
        return
    if "thumb" in name:
        _rr(draw, (W // 2 - 120, H // 2 - 60, W // 2 + 120, H // 2 + 60), t.accent, t.outline, 3, 14)
        return
    # key wells
    _rr(draw, (80, 120, W // 2 - 40, H - 80), (255, 255, 255, 255), t.outline, 3, 12)
    _rr(draw, (W // 2 + 40, 120, W - 80, H - 80), (255, 255, 255, 255), t.outline, 3, 12)


def _draw_keyboard(name: str, t: ThemeColors, draw, im) -> None:
    white = (255, 255, 255, 255)
    n = name.lower()
    if "keycap_blank_round" in n:
        _rr(draw, (W // 2 - 100, H // 2 - 100, W // 2 + 100, H // 2 + 100), t.surface_menu, t.outline, 3, 40)
        return
    if "keycap_blank_square" in n:
        draw.rectangle([W // 2 - 100, H // 2 - 100, W // 2 + 100, H // 2 + 100], fill=t.surface_menu, outline=t.outline, width=4)
        return
    _rr(draw, (40, 40, W - 40, H - 40), white, t.outline, 3, 12)
    if "numeric" in n:
        keys = [(c, r) for r in range(4) for c in range(4)]
    elif "symbols" in n:
        keys = [(c, r) for r in range(4) for c in range(12)]
    elif "compact" in n:
        keys = [(c, r) for r in range(3) for c in range(8)]
    else:
        keys = [(c, r) for r in range(3) for c in range(12)]
    margin_x, margin_y = 60, 80
    kw = (W - 2 * margin_x) // max(1, max(k[0] for k in keys) + 1)
    kh = (H - 2 * margin_y) // max(1, max(k[1] for k in keys) + 1)
    painted = "painted" in n
    for c, r in keys:
        x0 = margin_x + c * kw + (20 if r > 0 else 0)
        y0 = margin_y + r * kh
        fill = t.accent if painted and (c + r) % 4 == 0 else t.surface_menu
        rad = 22 if "round" in n or "plate" in n else 6
        if "square" in n and "keycap" in n:
            draw.rectangle([x0, y0, x0 + kw - 8, y0 + kh - 8], fill=fill, outline=t.outline, width=3)
        else:
            _rr(draw, (x0, y0, x0 + kw - 8, y0 + kh - 8), fill, t.outline, 2, rad if "round" in n or "plate" in n else 6)


def generate_one_png(rel_name: str, theme_key: str) -> Dict[str, Any]:
    from PIL import Image, ImageDraw

    t = THEMES[theme_key]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    name = rel_name.lower()

    try:
        if "sara_office_" in name:
            _draw_office(rel_name, t, draw, im)
        elif "sara_icon_app_" in name:
            _draw_icon_app(rel_name, t, draw, im)
        elif "sara_status_" in name:
            _draw_status(rel_name, t, draw, im)
        elif "sara_launcher" in name:
            _draw_launcher(rel_name, t, draw, im)
        elif "sara_secretary_" in name or "sara_marketing_" in name or "sara_accountant_" in name:
            _draw_app_panel(rel_name, t, draw, im)
        elif "sara_geek_" in name or "sara_football_" in name:
            _draw_geek_football(rel_name, t, draw, im)
        elif "sara_mapper_" in name:
            _draw_mapper(rel_name, t, draw, im)
        elif "sara_hid_joystick" in name:
            _draw_joystick(rel_name, t, draw, im)
        elif "sara_hid_macro" in name:
            _draw_macro(rel_name, t, draw, im)
        elif "sara_hid_steno" in name:
            _draw_steno(rel_name, t, draw, im)
        elif "sara_hid_keyboard" in name or "sara_hid_keycap" in name:
            _draw_keyboard(rel_name, t, draw, im)
        else:
            _rr(draw, (40, 40, W - 40, H - 40), t.surface, t.outline, 3, 12)

        _label(draw, rel_name, t, 8)
        out = OUT_PNG_DIR / rel_name
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, format="PNG")
    except Exception as e:
        with _lock:
            _errors.append(f"{rel_name}: {e}")
        raise

    rel_path = f"assets/png/{rel_name}"
    return {
        "id": rel_name.replace(".png", "").replace(".", "_"),
        "file": rel_path.replace("\\", "/"),
        "pixel_width": W,
        "pixel_height": H,
        "aspect": "4:3",
        "style_tags": ["procedural_bootstrap", "cartoon", theme_key],
        "logical_regions": {
            "safe_rect": {"x0": 0.5, "y0": 0.5, "x1": 9.5, "y1": 9.0},
            "slice_caps": {"left": 0.9, "right": 0.9, "top": 0.9, "bottom": 0.9},
            "hit_boxes": [],
        },
        "keys_drawn_in_art": "keyboard" in name and "painted" in name,
        "paint_brief": f"Bootstrap placeholder for {rel_name} ({theme_key}).",
    }


def write_themes_json() -> None:
    OUT_META_DIR.mkdir(parents=True, exist_ok=True)
    serializable = {
        "default_theme": "popcap_default",
        "selectable": list(THEMES.keys()),
        "notes": "SEC + Murray State entries are palette-only (no logos). Apps pick a theme key at runtime.",
        "themes": {k: {field: list(getattr(v, field)) for field in v.__dataclass_fields__} for k, v in THEMES.items()},
    }
    (OUT_META_DIR / "sara_themes.json").write_text(json.dumps(serializable, indent=2), encoding="utf-8")


def png_to_ico(src: Path, dst: Path) -> None:
    from PIL import Image

    if not src.is_file():
        raise FileNotFoundError(f"Desktop PNG not found: {src}")
    im = Image.open(src).convert("RGBA")
    sizes = [16, 32, 48, 64, 128, 256]
    frames = [im.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
    dst.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        dst,
        format="ICO",
        sizes=[(f.width, f.height) for f in frames],
        append_images=frames[1:],
    )
    print(f"[ico] wrote {dst}")


def main() -> int:
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("pip install pillow", file=sys.stderr)
        return 1

    theme_key = "popcap_default"
    OUT_PNG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_META_DIR.mkdir(parents=True, exist_ok=True)
    write_themes_json()
    print(f"[themes] wrote {OUT_META_DIR / 'sara_themes.json'}")

    meta_rows: List[Dict[str, Any]] = []
    max_workers = min(16, max(4, len(ASSET_FILENAMES) // 4))

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(generate_one_png, fn, theme_key): fn for fn in ASSET_FILENAMES}
        for fut in as_completed(futs):
            fn = futs[fut]
            try:
                meta_rows.append(fut.result())
                print(f"[png] ok {fn}")
            except Exception:
                print(f"[png] FAIL {fn}")

    meta_rows.sort(key=lambda r: r["file"])
    (OUT_META_DIR / "assets_meta.json").write_text(
        json.dumps({"assets": meta_rows}, indent=2),
        encoding="utf-8",
    )
    print(f"[meta] wrote {OUT_META_DIR / 'assets_meta.json'}")

    if _errors:
        print("[errors]", file=sys.stderr)
        for e in _errors:
            print(e, file=sys.stderr)

    try:
        png_to_ico(DESKTOP_PNG_FOR_ICO.expanduser().resolve(), ICO_OUT.resolve())
    except Exception as e:
        print(f"[ico] skipped: {e}", file=sys.stderr)

    return 0 if not _errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
