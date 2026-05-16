"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyProbeSystem = void 0;
const vscode = require("vscode");
const deviceListener_1 = require("../devices/deviceListener");
const profileManager_1 = require("../profiles/profileManager");
const macroRegistry_1 = require("../macros/macroRegistry");
const ipcClient_1 = require("../ipc/ipcClient");
function smithyProbeSystem() {
    var _a;
    return __awaiter(this, void 0, void 0, function* () {
        const results = [];
        // 1. Workspace check
        const workspace = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0];
        if (!workspace) {
            vscode.window.showErrorMessage("Smithy Probe: No workspace open.");
            return;
        }
        results.push("✔ Workspace detected");
        // 2. Profile load test
        try {
            const profile = profileManager_1.ProfileManager.loadProfile();
            results.push("✔ Profile loaded: " + profile.name);
        }
        catch (err) {
            results.push("✖ Profile load failed: " + err);
        }
        // 3. Macro registry test
        try {
            macroRegistry_1.MacroRegistry.register("probe.test", {
                id: "probe.test",
                action: "blender:ping",
                payload: { probe: true }
            });
            results.push("✔ Macro registry operational");
        }
        catch (err) {
            results.push("✖ Macro registry failed: " + err);
        }
        // 4. Device listener test
        try {
            deviceListener_1.DeviceListener.start();
            deviceListener_1.DeviceListener.handleRawInput({
                device: "Probe",
                control: "Test",
                value: 1
            });
            results.push("✔ Device Listener operational");
        }
        catch (err) {
            results.push("✖ Device Listener failed: " + err);
        }
        // 5. IPC dispatch test
        try {
            ipcClient_1.IPCClient.send({
                target: "blender",
                command: "probe_ping",
                payload: { time: Date.now() }
            });
            results.push("✔ IPC dispatch operational");
        }
        catch (err) {
            results.push("✖ IPC dispatch failed: " + err);
        }
        // 6. UI test (Profile Editor)
        try {
            yield vscode.commands.executeCommand("smithy.openProfileEditor");
            results.push("✔ Profile Editor UI loaded");
        }
        catch (err) {
            results.push("✖ Profile Editor UI failed: " + err);
        }
        // Final report
        const output = results.join("\n");
        vscode.window.showInformationMessage("Smithy Probe Complete — see output panel.");
        const channel = vscode.window.createOutputChannel("Smithy Probe");
        channel.clear();
        channel.appendLine("=== SMITHY SYSTEM PROBE ===");
        channel.appendLine(output);
        channel.show(true);
    });
}
exports.smithyProbeSystem = smithyProbeSystem;
//# sourceMappingURL=probeSystem.js.map