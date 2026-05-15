# 06 SARA Bridge — Smithy Core Extension

## Command Routing Model
- All commands from VS Code (Smithy) destined for SARA are routed through the Smithy core extension.
- Device input, macros, and VS Code commands are normalized and dispatched as SARA actions.
- No direct communication between Blender and SARA; all traffic is mediated by Smithy.

## Actionmap Integration
- The Smithy core extension loads and manages SARA actionmaps (JSON or schema-based).
- Actionmaps define available SARA actions, parameters, and device/command bindings.
- Dynamic updates to the actionmap are supported (e.g., hot-reload on file change).

## State Query Model
- VS Code can query SARA for current state (e.g., session, profile, active tools) via Smithy commands.
- State queries return normalized JSON objects for use in logs, UI, or automation.

## Logging Rules
- All command routing, action invocations, and state queries are logged by the Smithy core extension.
- Logs include timestamps, command sources, payloads, and SARA responses.
- Logging can be toggled or filtered by profile or session.

## Example Commands

### `sara.runAction`
- Runs a specific SARA action.
```json
{
  "command": "sara.runAction",
  "action": "exportProfile",
  "params": { "profileId": "user1" }
}
```

### `sara.queryState`
- Queries SARA for current state.
```json
{
  "command": "sara.queryState",
  "query": "activeProfile"
}
```

### `sara.loadMapping`
- Loads a new actionmap or device mapping into SARA.
```json
{
  "command": "sara.loadMapping",
  "mappingFile": "profiles/gaming_profile.json"
}
```

### `sara.executeBatch`
- Executes a batch of SARA actions atomically.
```json
{
  "command": "sara.executeBatch",
  "actions": [
    { "action": "saveProfile" },
    { "action": "exportProfile", "params": { "profileId": "user1" } }
  ]
}
```

---

- All SARA bridge commands are invoked from VS Code and routed through the Smithy core extension.
- Actionmap and state query models enable advanced automation and integration.
- Logging ensures traceability and debugging support for all SARA-related operations.
