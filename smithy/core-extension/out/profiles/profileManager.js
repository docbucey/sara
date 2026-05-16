"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProfileManager = void 0;
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
class ProfileManager {
    static getProfilePath() {
        var _a;
        const folder = ((_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0].uri.fsPath) || '';
        return path.join(folder, ProfileManager.profileFile);
    }
    static loadProfile() {
        const file = ProfileManager.getProfilePath();
        if (!fs.existsSync(file)) {
            return { name: "default", mappings: {} };
        }
        return JSON.parse(fs.readFileSync(file, 'utf8'));
    }
    static saveProfile(profile) {
        const file = ProfileManager.getProfilePath();
        fs.writeFileSync(file, JSON.stringify(profile, null, 2));
    }
}
exports.ProfileManager = ProfileManager;
ProfileManager.profileFile = 'smithy_profile.json';
//# sourceMappingURL=profileManager.js.map