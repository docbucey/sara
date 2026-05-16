"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerSaveProfile = void 0;
const vscode = require("vscode");
function registerSaveProfile(context) {
    context.subscriptions.push(vscode.commands.registerCommand('smithy.saveProfile', () => {
        vscode.window.showInformationMessage('Profile saved.');
    }));
}
exports.registerSaveProfile = registerSaveProfile;
//# sourceMappingURL=saveProfile.js.map