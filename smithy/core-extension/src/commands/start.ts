import * as vscode from 'vscode';
export function registerStart(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('smithy.start', () => {
      vscode.window.showInformationMessage('Smithy started.');
    })
  );
}
