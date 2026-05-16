"""
SARA SDK — Macro Engine
Ported from DisabilityMapper/Services/MacroEngine.cs

Executes mapped actions: KeyPress, MouseClick, MouseMove, MacroText,
Command, StenoToggle.  Platform input injection uses ctypes on Windows
(no external dependency needed).
"""

import asyncio
import ctypes
import ctypes.wintypes
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


# ── Win32 SendInput structures ──────────────────────────────────────────────

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_MOVE = 0x0001

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD), ("union", _INPUT_UNION)]


def _send_input(*inputs: INPUT) -> None:
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(INPUT))


def _key_down(vk: int) -> None:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    _send_input(inp)


def _key_up(vk: int) -> None:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    inp.union.ki.dwFlags = KEYEVENTF_KEYUP
    _send_input(inp)


def _key_press(vk: int) -> None:
    _key_down(vk)
    _key_up(vk)


def _char_entry(ch: str) -> None:
    down = INPUT()
    down.type = INPUT_KEYBOARD
    down.union.ki.wScan = ord(ch)
    down.union.ki.dwFlags = KEYEVENTF_UNICODE
    up = INPUT()
    up.type = INPUT_KEYBOARD
    up.union.ki.wScan = ord(ch)
    up.union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
    _send_input(down, up)


def _mouse_event(flags: int, dx: int = 0, dy: int = 0) -> None:
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi.dx = dx
    inp.union.mi.dy = dy
    inp.union.mi.dwFlags = flags
    _send_input(inp)


# ── Common VK name → code mapping ──────────────────────────────────────────

_VK_MAP = {
    "BACK": 0x08, "TAB": 0x09, "RETURN": 0x0D, "ESCAPE": 0x1B,
    "SPACE": 0x20, "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    "DELETE": 0x2E, "HOME": 0x24, "END": 0x23, "PRIOR": 0x21, "NEXT": 0x22,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74,
    "F6": 0x75, "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79,
    "F11": 0x7A, "F12": 0x7B,
    "LSHIFT": 0xA0, "RSHIFT": 0xA1, "LCONTROL": 0xA2, "RCONTROL": 0xA3,
    "LMENU": 0xA4, "RMENU": 0xA5, "LWIN": 0x5B, "RWIN": 0x5C,
}
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    _VK_MAP[c] = ord(c)
for d in "0123456789":
    _VK_MAP[d] = ord(d)


def _resolve_vk(name: str) -> Optional[int]:
    return _VK_MAP.get(name.upper())


# ── MappingAction dataclass ────────────────────────────────────────────────

@dataclass
class MappingAction:
    type: str = "KeyPress"
    value: str = ""
    hold_mode: bool = False
    macro_text: str = ""
    macro_delay_ms: int = 30
    macro_jitter_ms: int = 5

    @classmethod
    def from_dict(cls, d: dict) -> "MappingAction":
        return cls(
            type=d.get("type", d.get("Type", "KeyPress")),
            value=d.get("value", d.get("Value", "")),
            hold_mode=d.get("hold_mode", d.get("HoldMode", False)),
            macro_text=d.get("macro_text", d.get("MacroText", "")),
            macro_delay_ms=d.get("macro_delay_ms", d.get("MacroDelayMs", 30)),
            macro_jitter_ms=d.get("macro_jitter_ms", d.get("MacroJitterMs", 5)),
        )


# ── MacroEngine ────────────────────────────────────────────────────────────

class MacroEngine:
    """Executes MappingAction objects by injecting input via Win32 SendInput."""

    def __init__(self):
        self.steno_toggle_callback: Optional[Callable[[], None]] = None

    async def execute(self, action: MappingAction, is_press: bool) -> None:
        if action.type == "KeyPress":
            self._key_press(action, is_press)
        elif action.type == "MouseClick":
            self._mouse_click(action, is_press)
        elif action.type == "MouseMove":
            self._mouse_move(action)
        elif action.type == "MacroText" and is_press:
            await self._macro_text(action)
        elif action.type == "Command" and is_press:
            self._command(action)
        elif action.type == "StenoToggle" and is_press:
            if self.steno_toggle_callback:
                self.steno_toggle_callback()

    def execute_sync(self, action: MappingAction, is_press: bool) -> None:
        if action.type == "KeyPress":
            self._key_press(action, is_press)
        elif action.type == "MouseClick":
            self._mouse_click(action, is_press)
        elif action.type == "MouseMove":
            self._mouse_move(action)
        elif action.type == "MacroText" and is_press:
            self._macro_text_sync(action)
        elif action.type == "Command" and is_press:
            self._command(action)
        elif action.type == "StenoToggle" and is_press:
            if self.steno_toggle_callback:
                self.steno_toggle_callback()

    def _key_press(self, action: MappingAction, is_press: bool) -> None:
        vk = _resolve_vk(action.value)
        if vk is None:
            return
        if action.hold_mode:
            (_key_down if is_press else _key_up)(vk)
        elif is_press:
            _key_press(vk)

    def _mouse_click(self, action: MappingAction, is_press: bool) -> None:
        btn = action.value.lower()
        if btn == "left":
            if action.hold_mode:
                _mouse_event(MOUSEEVENTF_LEFTDOWN if is_press else MOUSEEVENTF_LEFTUP)
            elif is_press:
                _mouse_event(MOUSEEVENTF_LEFTDOWN)
                _mouse_event(MOUSEEVENTF_LEFTUP)
        elif btn == "right":
            if action.hold_mode:
                _mouse_event(MOUSEEVENTF_RIGHTDOWN if is_press else MOUSEEVENTF_RIGHTUP)
            elif is_press:
                _mouse_event(MOUSEEVENTF_RIGHTDOWN)
                _mouse_event(MOUSEEVENTF_RIGHTUP)
        elif btn == "middle" and is_press:
            _mouse_event(MOUSEEVENTF_MIDDLEDOWN)
            _mouse_event(MOUSEEVENTF_MIDDLEUP)

    def _mouse_move(self, action: MappingAction) -> None:
        parts = action.value.split(",")
        if len(parts) == 2:
            try:
                dx, dy = int(parts[0]), int(parts[1])
                _mouse_event(MOUSEEVENTF_MOVE, dx, dy)
            except ValueError:
                pass

    async def _macro_text(self, action: MappingAction) -> None:
        if not action.macro_text:
            return
        for ch in action.macro_text:
            _char_entry(ch)
            delay = action.macro_delay_ms
            if action.macro_jitter_ms > 0:
                delay += random.randint(-action.macro_jitter_ms, action.macro_jitter_ms)
            delay = max(0, delay)
            if delay > 0:
                await asyncio.sleep(delay / 1000.0)

    def _macro_text_sync(self, action: MappingAction) -> None:
        if not action.macro_text:
            return
        for ch in action.macro_text:
            _char_entry(ch)
            delay = action.macro_delay_ms
            if action.macro_jitter_ms > 0:
                delay += random.randint(-action.macro_jitter_ms, action.macro_jitter_ms)
            delay = max(0, delay)
            if delay > 0:
                time.sleep(delay / 1000.0)

    def inject_raw(self, text: str) -> None:
        if not text:
            return
        for ch in text:
            if ch == "\b":
                _key_press(VK_BACK)
            elif ch in ("\r", "\n"):
                _key_press(VK_RETURN)
            elif ch == "\t":
                _key_press(VK_TAB)
            else:
                _char_entry(ch)

    def _command(self, action: MappingAction) -> None:
        if not action.value.strip():
            return
        import subprocess
        subprocess.Popen(
            ["cmd.exe", "/c", action.value],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
