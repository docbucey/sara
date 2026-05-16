"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerStart = void 0;
const vscode = require("vscode");
function registerStart(context) {
    context.subscriptions.push(vscode.commands.registerCommand('smithy.start', () => {
        vscode.window.showInformationMessage('Smithy started.');
    }));
}
exports.registerStart = registerStart;
//# sourceMappingURL=start.js.map