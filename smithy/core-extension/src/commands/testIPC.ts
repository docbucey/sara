import * as vscode from 'vscode';
import { IPCClient } from '../ipc/ipcClient';

export function smithyTestIPC() {
    IPCClient.send({
        target: "blender",
        command: "ping",
        payload: { time: Date.now() }
    });

    vscode.window.showInformationMessage("Smithy IPC test sent.");
}
