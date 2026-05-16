import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export interface SmithyProfile {
    name: string;
    mappings: Record<string, string>;
}

export class ProfileManager {
    private static profileFile = 'smithy_profile.json';

    static getProfilePath(): string {
        const folder = vscode.workspace.workspaceFolders?.[0].uri.fsPath || '';
        return path.join(folder, ProfileManager.profileFile);
    }

    static loadProfile(): SmithyProfile {
        const file = ProfileManager.getProfilePath();
        if (!fs.existsSync(file)) {
            return { name: "default", mappings: {} };
        }
        return JSON.parse(fs.readFileSync(file, 'utf8'));
    }

    static saveProfile(profile: SmithyProfile) {
        const file = ProfileManager.getProfilePath();
        fs.writeFileSync(file, JSON.stringify(profile, null, 2));
    }
}
