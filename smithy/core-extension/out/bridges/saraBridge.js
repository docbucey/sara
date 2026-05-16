"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sendToSara = void 0;
function sendToSara(action, payload = {}) {
    console.log("[Smithy] SARA Bridge →", action, payload);
    // IPC/WebSocket placeholder
    IPCClient.send({
        target: "sara",
        command: action,
        payload
    });
}
exports.sendToSara = sendToSara;
//# sourceMappingURL=saraBridge.js.map