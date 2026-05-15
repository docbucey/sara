# Smithy Core Extension

Smithy is a VS Code cockpit for orchestrating Blender, SARA, and device-driven workflows.

## Features
- Device input mapping (G13, HOTAS, mouse, voice)
- Profile system (JSON-based)
- Command routing to Blender and SARA
- Maya-mode integration points
- Macro engine stubs
- IPC-ready bridge architecture

## Commands
- smithy.start
- smithy.sendToBlender
- smithy.sendToSara
- smithy.bindDeviceInput
- smithy.runMacro
- smithy.loadProfile
- smithy.saveProfile

## Architecture
VS Code is the master control surface.
Blender and SARA are slave tools.
All device input flows into Smithy first.
All commands flow outward from Smithy.
