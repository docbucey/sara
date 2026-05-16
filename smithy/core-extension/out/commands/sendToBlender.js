"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerSendToBlender = void 0;
const vscode = require("vscode");
function registerSendToBlender(context) {
    context.subscriptions.push(vscode.commands.registerCommand('smithy.sendToBlender', () => {
        vscode.window.showInformationMessage('Sent to Blender.');
    }));
}
exports.registerSendToBlender = registerSendToBlender;
//# sourceMappingURL=sendToBlender.js.map