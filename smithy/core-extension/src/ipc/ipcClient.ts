import { SmithyIPCMessage } from "./ipcTypes";

export class IPCClient {
    static send(msg: SmithyIPCMessage) {
        console.log("[Smithy IPC] →", JSON.stringify(msg, null, 2));

        // Placeholder for future IPC transport:
        // - WebSocket
        // - Named pipes
        // - Local RPC
        // - Child process messaging
    }
}
