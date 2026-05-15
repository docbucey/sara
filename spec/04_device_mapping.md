# 04 Device Mapping — Smithy Core Extension

## Input Normalization Model
All device inputs are normalized to a common event structure before processing. This enables consistent mapping and handling regardless of device type or vendor.

**Normalized Input Event Example:**
```json
{
  "device": "G13",
  "type": "button",
  "id": "G13_BTN_5",
  "value": 1,
  "timestamp": 1714150000
}
```

## Device Categories
- **G13**: Keypad (buttons, joystick)
- **HOTAS**: Flight stick/throttle (axes, buttons, hats)
- **Mouse**: Buttons, wheel, movement
- **Voice**: Recognized phrases mapped to actions

## Profile System
- Users can create, load, and save device mapping profiles.
- Profiles define how device inputs are mapped to Smithy commands/macros.
- Profiles can be switched on-the-fly for different workflows or games.

## Conflict Resolution Rules
- If multiple devices map to the same command, all can trigger it.
- If multiple commands are mapped to the same input, the profile's priority order is used.
- Device-specific overrides take precedence over global mappings.
- Warnings are shown for ambiguous/conflicting mappings during profile load.

## Mapping Format (JSON)
Mappings are stored as JSON objects, associating normalized device events with Smithy commands/macros.

**Mapping Format Example:**
```json
{
  "G13_BTN_5": "smithy.sendToBlender",
  "HOTAS_AXIS_X+": "smithy.runMacro:rollRight",
  "MOUSE_BTN_4": "smithy.openLog",
  "VOICE:export": "smithy.sendToSara"
}
```

## Example Mappings
```json
{
  "G13_BTN_1": "smithy.start",
  "G13_BTN_2": "smithy.stop",
  "HOTAS_BTN_1": "smithy.sendToBlender",
  "HOTAS_AXIS_Y+": "smithy.runMacro:throttleUp",
  "MOUSE_BTN_3": "smithy.openSessionFolder",
  "VOICE:save profile": "smithy.saveProfile"
}
```

---

- All device mappings are editable and can be exported/imported as JSON profiles.
- Voice commands are prefixed with `VOICE:` and matched against recognized phrases.
- Device and command IDs are case-insensitive.
