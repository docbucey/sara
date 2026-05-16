import * as vscode from 'vscode';
export function registerSendToBlender(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('smithy.sendToBlender', () => {
      vscode.window.showInformationMessage('Sent to Blender.');
    })
  );
}
