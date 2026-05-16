import * as vscode from 'vscode';
export function registerStop(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('smithy.stop', () => {
      vscode.window.showInformationMessage('Smithy stopped.');
    })
  );
}
