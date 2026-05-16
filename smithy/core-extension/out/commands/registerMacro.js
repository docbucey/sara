"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyRegisterMacro = void 0;
const vscode = require("vscode");
const macroRegistry_1 = require("../macros/macroRegistry");
function smithyRegisterMacro(id, action, payload = {}) {
    macroRegistry_1.MacroRegistry.register(id, {
        id,
        action,
        payload
    });
    vscode.window.showInformationMessage(`Smithy: Macro "${id}" registered.`);
}
exports.smithyRegisterMacro = smithyRegisterMacro;
//# sourceMappingURL=registerMacro.js.map