# SARA Gaming & HelixToolkit Integration

## Overview
This library provides the foundation for SARA's calibration games, 3D visualization, and plugin integration using HelixToolkit for C#.

## Folder Structure
- Graphics/ : Rendering, window management, HelixToolkit integration
- Models/   : STL/OBJ/3D model loaders and sample assets
- Games/Calibration/ : Calibration and adaptation games (reaction, aiming, navigation)
- Input/    : Device abstraction, mapping, and event capture
- Utils/    : Math, geometry, and timing utilities

## HelixToolkit Specs
- Use HelixToolkit.Wpf or HelixToolkit.SharpDX for 3D rendering and model loading
- Support STL, OBJ, 3DS, and other common 3D formats
- Provide camera controls, scene graph, and manipulators for calibration and adaptation
- Integrate with SARA's SDK and MAMA pillars for device mapping and ADA overlays

## Blender Plugin Integration
- Develop a C# plugin that embeds Blender as a side panel within the SARA workspace
- Enable HelixToolkit-powered 3D previews and manipulation alongside Blender's native tools
- Allow Blender to act as a side panel for MS Office, VS Code, and other plugins
- SARA Copilot/AI can automate, script, or guide Blender workflows for accessibility and productivity

## Example Calibration Games
- ReactionGame.cs: Measures input latency and reaction time
- AimingGame.cs: Tests accuracy and speed with various input devices
- NavigationGame.cs: Evaluates spatial navigation and control mapping

## Build/Integration
- Add HelixToolkit, AssimpNet, and MonoGame via NuGet
- Ensure all modules are discoverable by SARA's SDK/MAMA for calibration and adaptation

---
For more details, see the Graphics/ and Games/Calibration/ folders for starter code and integration points.
