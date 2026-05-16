import { DeviceEvent } from "./deviceEvent";
import { normalizeInput } from "./inputNormalizer";
import { ProfileManager } from "../profiles/profileManager";
import { smithyRunMacro } from "../commands/runMacro";

export class DeviceListener {
    private static active = false;

    static start() {
        if (this.active) return;
        this.active = true;
        console.log("[Smithy] Device Listener Engine started.");
    }

    static stop() {
        this.active = false;
        console.log("[Smithy] Device Listener Engine stopped.");
    }

    static handleRawInput(raw: any) {
        if (!this.active) return;

        const normalized = normalizeInput(raw);
        console.log("[Smithy] Normalized Input:", normalized);

        const profile = ProfileManager.loadProfile();
        const key = `${normalized.device}.${normalized.control}`;

        if (profile.mappings[key]) {
            smithyRunMacro(profile.mappings[key]);
        }
    }
}
