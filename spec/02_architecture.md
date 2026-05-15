# 02 Architecture

## Master/Slave Architecture

- **VS Code (Smithy)** is the master cockpit.
- **Blender** and **SARA** are slave tools.
- All device input (G13, HOTAS, mouse, voice) routes into VS Code first.
- VS Code sends commands to Blender and SARA through the core extension.
- Blender never talks directly to SARA.
- SARA never talks directly to Blender.
- All traffic flows through the Smithy core extension.

## Data Flow

1. Device input (G13, HOTAS, mouse, voice) → VS Code (Smithy)
2. VS Code (Smithy) → Smithy core extension
3. Smithy core extension → Blender or SARA (as appropriate)

## Notes
- This architecture enforces strict separation: Blender and SARA are not aware of each other and only communicate via VS Code.
- All orchestration, automation, and integration logic resides in the Smithy core extension.
