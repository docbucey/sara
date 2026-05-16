import * as vscode from 'vscode';
import { MacroRegistry } from '../macros/macroRegistry';
import { MacroEngine } from '../macros/macroEngine';

export function smithyRunMacro(id: string) {
    const macro = MacroRegistry.get(id);

    if (!macro) {
        vscode.window.showWarningMessage(`Smithy: Unknown macro "${id}"`);
        return;
    }

    MacroEngine.run(macro);
}
}
