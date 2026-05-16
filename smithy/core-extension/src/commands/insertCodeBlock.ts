import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export async function smithyInsertCodeBlock(
    filePath: string,
    code: string
) {
    const workspace = vscode.workspace.workspaceFolders?.[0];
    if (!workspace) {
        vscode.window.showErrorMessage("Smithy: No workspace open.");
        return;
    }

    const fullPath = path.join(workspace.uri.fsPath, filePath);

    // Ensure folder exists
    const dir = path.dirname(fullPath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }

    // Create file if missing
    if (!fs.existsSync(fullPath)) {
        fs.writeFileSync(fullPath, "");
    }

    // Open the file in VS Code
    const doc = await vscode.workspace.openTextDocument(fullPath);
    const editor = await vscode.window.showTextDocument(doc);

    // Insert code at end of file
    const lastLine = doc.lineCount;
    const position = new vscode.Position(lastLine, 0);

    await editor.edit(editBuilder => {
        editBuilder.insert(position, "\n" + code + "\n");
    });

    vscode.window.showInformationMessage(`Smithy: Code inserted into ${filePath}`);
}
