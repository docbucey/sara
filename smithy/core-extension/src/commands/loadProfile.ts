import * as vscode from 'vscode';
export function registerLoadProfile(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('smithy.loadProfile', () => {
      vscode.window.showInformationMessage('Profile loaded.');
    })
  );
}
