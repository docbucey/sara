
import * as vscode from 'vscode';
import { registerCommands } from './commands/registerCommands';

export function activate(context: vscode.ExtensionContext) {
    // Status bar item
    const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBar.text = '$(tools) Smithy';
    statusBar.tooltip = 'Smithy Core Extension Active';
    statusBar.show();
    context.subscriptions.push(statusBar);

    // Register all commands
    registerCommands(context);
}

export function deactivate() {
    // Nothing yet — add cleanup if needed later
}
