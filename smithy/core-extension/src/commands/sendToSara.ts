import * as vscode from 'vscode';
export function registerSendToSara(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('smithy.sendToSara', () => {
      vscode.window.showInformationMessage('Sent to SARA.');
    })
  );
}
