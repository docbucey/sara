"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sendToBlender = void 0;
function sendToBlender(command, payload = {}) {
    console.log("[Smithy] Blender Bridge →", command, payload);
    // IPC/WebSocket placeholder
}
exports.sendToBlender = sendToBlender;
const ipcClient_1 = require("../ipc/ipcClient");
function sendToBlender(command, payload = {}) {
    ipcClient_1.IPCClient.send({
        target: "blender",
        command,
        payload
    });
}
exports.sendToBlender = sendToBlender;
//# sourceMappingURL=blenderBridge.js.map