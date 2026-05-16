import * as vscode from 'vscode';
import { DeviceListener } from '../devices/deviceListener';
import { ProfileManager } from '../profiles/profileManager';
import { MacroRegistry } from '../macros/macroRegistry';
import { IPCClient } from '../ipc/ipcClient';

export async function smithyProbeSystem() {
    const results: string[] = [];

    // 1. Workspace check
    const workspace = vscode.workspace.workspaceFolders?.[0];
    if (!workspace) {
        vscode.window.showErrorMessage("Smithy Probe: No workspace open.");
        return;
    }
    results.push("✔ Workspace detected");

    // 2. Profile load test
    try {
        const profile = ProfileManager.loadProfile();
        results.push("✔ Profile loaded: " + profile.name);
    } catch (err) {
        results.push("✖ Profile load failed: " + err);
    }

    // 3. Macro registry test
    try {
        MacroRegistry.register("probe.test", {
            id: "probe.test",
            action: "blender:ping",
            payload: { probe: true }
        });
        results.push("✔ Macro registry operational");
    } catch (err) {
        results.push("✖ Macro registry failed: " + err);
    }

    // 4. Device listener test
    try {
        DeviceListener.start();
        DeviceListener.handleRawInput({
            device: "Probe",
            control: "Test",
            value: 1
        });
        results.push("✔ Device Listener operational");
    } catch (err) {
        results.push("✖ Device Listener failed: " + err);
    }

    // 5. IPC dispatch test
    try {
        IPCClient.send({
            target: "blender",
            command: "probe_ping",
            payload: { time: Date.now() }
        });
        results.push("✔ IPC dispatch operational");
    } catch (err) {
        results.push("✖ IPC dispatch failed: " + err);
    }

    // 6. UI test (Profile Editor)
    try {
        await vscode.commands.executeCommand("smithy.openProfileEditor");
        results.push("✔ Profile Editor UI loaded");
    } catch (err) {
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
}
