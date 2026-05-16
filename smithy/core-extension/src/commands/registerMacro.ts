import * as vscode from 'vscode';
import { MacroRegistry } from '../macros/macroRegistry';

export function smithyRegisterMacro(id: string, action: string, payload: any = {}) {
    MacroRegistry.register(id, {
        id,
        action,
        payload
    });

    vscode.window.showInformationMessage(`Smithy: Macro "${id}" registered.`);
}
