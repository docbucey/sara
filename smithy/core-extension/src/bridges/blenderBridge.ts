export function sendToBlender(command: string, payload: any = {}) {
    console.log("[Smithy] Blender Bridge →", command, payload);
    // IPC/WebSocket placeholder
}
import { IPCClient } from "../ipc/ipcClient";

export function sendToBlender(command: string, payload: any = {}) {
    IPCClient.send({
        target: "blender",
        command,
        payload
    });
}
