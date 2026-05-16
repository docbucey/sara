"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerSendToSara = void 0;
const vscode = require("vscode");
function registerSendToSara(context) {
    context.subscriptions.push(vscode.commands.registerCommand('smithy.sendToSara', () => {
        vscode.window.showInformationMessage('Sent to SARA.');
    }));
}
exports.registerSendToSara = registerSendToSara;
//# sourceMappingURL=sendToSara.js.map