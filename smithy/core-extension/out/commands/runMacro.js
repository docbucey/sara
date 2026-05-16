"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyRunMacro = void 0;
const vscode = require("vscode");
const macroRegistry_1 = require("../macros/macroRegistry");
const macroEngine_1 = require("../macros/macroEngine");
function smithyRunMacro(id) {
    const macro = macroRegistry_1.MacroRegistry.get(id);
    if (!macro) {
        vscode.window.showWarningMessage(`Smithy: Unknown macro "${id}"`);
        return;
    }
    macroEngine_1.MacroEngine.run(macro);
}
exports.smithyRunMacro = smithyRunMacro;
//# sourceMappingURL=runMacro.js.map