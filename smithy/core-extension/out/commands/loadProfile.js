"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerLoadProfile = void 0;
const vscode = require("vscode");
function registerLoadProfile(context) {
    context.subscriptions.push(vscode.commands.registerCommand('smithy.loadProfile', () => {
        vscode.window.showInformationMessage('Profile loaded.');
    }));
}
exports.registerLoadProfile = registerLoadProfile;
//# sourceMappingURL=loadProfile.js.map