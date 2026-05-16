"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IPCClient = void 0;
class IPCClient {
    static send(msg) {
        console.log("[Smithy IPC] →", JSON.stringify(msg, null, 2));
        // Placeholder for future IPC transport:
        // - WebSocket
        // - Named pipes
        // - Local RPC
        // - Child process messaging
    }
}
exports.IPCClient = IPCClient;
//# sourceMappingURL=ipcClient.js.map