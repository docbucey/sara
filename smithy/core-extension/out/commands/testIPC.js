"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyTestIPC = void 0;
const vscode = require("vscode");
const ipcClient_1 = require("../ipc/ipcClient");
function smithyTestIPC() {
    ipcClient_1.IPCClient.send({
        target: "blender",
        command: "ping",
        payload: { time: Date.now() }
    });
    vscode.window.showInformationMessage("Smithy IPC test sent.");
}
exports.smithyTestIPC = smithyTestIPC;
//# sourceMappingURL=testIPC.js.map