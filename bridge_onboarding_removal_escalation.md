# Onboarding, Removal, and Escalation Procedures for SARA Bridge Plugins

## Onboarding a New Environment/Plugin
1. Define the new plugin/envoy in citizens_template.json or envoys_template.json with minimal, explicit permissions.
2. Register the plugin with CONTROL, specifying its entrypoint and allowed actions.
3. CONTROL validates and logs the onboarding event in the NBS system.
4. Test the plugin to ensure it only performs allowed actions and all requests are audited.

## Removing/Disabling a Plugin
1. Update the template to remove or disable the plugin definition.
2. CONTROL revokes access and logs the removal event in the NBS system.
3. Confirm that the plugin can no longer communicate with CONTROL or access the NBS.

## Escalation Procedures
1. If a plugin requests an action outside its permissions (e.g., write/append), CONTROL blocks the action and logs the attempt.
2. CONTROL notifies an admin (per profile system) for review.
3. Admin can approve a temporary override, which is logged and time-limited.
4. All escalations and overrides are tracked in the NBS for audit.

---

This process ensures all plugins are governed, auditable, and easily managed as your system evolves.
