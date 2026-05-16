"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DeviceListener = void 0;
const inputNormalizer_1 = require("./inputNormalizer");
const profileManager_1 = require("../profiles/profileManager");
const runMacro_1 = require("../commands/runMacro");
class DeviceListener {
    static start() {
        if (this.active)
            return;
        this.active = true;
        console.log("[Smithy] Device Listener Engine started.");
    }
    static stop() {
        this.active = false;
        console.log("[Smithy] Device Listener Engine stopped.");
    }
    static handleRawInput(raw) {
        if (!this.active)
            return;
        const normalized = (0, inputNormalizer_1.normalizeInput)(raw);
        console.log("[Smithy] Normalized Input:", normalized);
        const profile = profileManager_1.ProfileManager.loadProfile();
        const key = `${normalized.device}.${normalized.control}`;
        if (profile.mappings[key]) {
            (0, runMacro_1.smithyRunMacro)(profile.mappings[key]);
        }
    }
}
exports.DeviceListener = DeviceListener;
DeviceListener.active = false;
//# sourceMappingURL=deviceListener.js.map