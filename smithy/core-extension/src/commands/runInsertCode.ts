import * as vscode from 'vscode';
import { smithyInsertCodeBlock } from './insertCodeBlock';

export function smithyRunInsertCode() {
    vscode.window.showInputBox({
        prompt: "Enter file path (relative to workspace)"
    }).then(filePath => {
        if (!filePath) return;

        vscode.window.showInputBox({
            prompt: "Paste the code block to insert"
        }).then(code => {
            if (!code) return;

            smithyInsertCodeBlock(filePath, code);
        });
    });
}
