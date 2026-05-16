"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerStop = void 0;
const vscode = require("vscode");
function registerStop(context) {
    context.subscriptions.push(vscode.commands.registerCommand('smithy.stop', () => {
        vscode.window.showInformationMessage('Smithy stopped.');
    }));
}
exports.registerStop = registerStop;
//# sourceMappingURL=stop.js.map