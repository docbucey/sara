# HelixToolkit Integration Specs for SARA

## Purpose
- Provide 3D rendering, model loading, and scene management for SARA calibration games and plugin panels.
- Enable advanced camera controls, manipulators, and ADA overlays for accessibility.

## Key Features
- Load and render STL, OBJ, 3DS, and other 3D formats (via HelixToolkit.Wpf or HelixToolkit.SharpDX)
- Scene graph with support for lighting, materials, and camera navigation
- Custom manipulators for calibration, input mapping, and accessibility
- Integration hooks for SARA Copilot/AI to automate or guide user actions
- Support for embedding HelixToolkit-powered views as side panels in Blender, MS Office, and VS Code plugins

## Example Use Cases
- 3D calibration games (reaction, aiming, navigation) with real-time feedback
- ADA overlays (high-contrast, large controls, alternative input)
- Copilot-driven automation (e.g., auto-align, snap, measure, or annotate models)
- Blender plugin: HelixToolkit-powered 3D preview and manipulation alongside Blender’s native tools
- Side panel integration: Blender as a panel in Office, VS Code, or other SARA plugins

## Integration Points
- Expose HelixToolkit controls as WPF UserControls or WinForms controls
- Use SARA SDK for device mapping and event routing
- Allow Copilot/AI to inject commands, scripts, or UI overlays

## Libraries
- [HelixToolkit.Wpf](https://github.com/helix-toolkit/helix-toolkit)
- [HelixToolkit.SharpDX](https://github.com/helix-toolkit/helix-toolkit)
- [AssimpNet](https://github.com/assimp/assimp-net) (for additional 3D format support)
