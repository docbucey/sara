"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const registerCommands_1 = require("./commands/registerCommands");
function activate(context) {
    // Status bar item
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBar.text = '$(tools) Smithy';
    statusBar.tooltip = 'Smithy Core Extension Active';
    statusBar.show();
    context.subscriptions.push(statusBar);
    // Register all commands
    (0, registerCommands_1.registerCommands)(context);
}
exports.activate = activate;
function deactivate() {
    // Nothing yet — add cleanup if needed later
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map