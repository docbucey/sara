"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerBindDeviceInput = void 0;
const vscode = require("vscode");
function registerBindDeviceInput(context) {
    context.subscriptions.push(vscode.commands.registerCommand('smithy.bindDeviceInput', () => {
        vscode.window.showInformationMessage('Device input bound.');
    }));
}
exports.registerBindDeviceInput = registerBindDeviceInput;
//# sourceMappingURL=bindDeviceInput.js.map