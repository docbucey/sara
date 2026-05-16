import * as vscode from 'vscode';
export function registerBindDeviceInput(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('smithy.bindDeviceInput', () => {
      vscode.window.showInformationMessage('Device input bound.');
    })
  );
}
