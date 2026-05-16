import * as vscode from 'vscode';
export function registerSaveProfile(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('smithy.saveProfile', () => {
      vscode.window.showInformationMessage('Profile saved.');
    })
  );
}
