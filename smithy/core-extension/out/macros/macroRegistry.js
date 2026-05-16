"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MacroRegistry = void 0;
class MacroRegistry {
    static register(id, macro) {
        this.macros[id] = macro;
        console.log("[Smithy] Macro registered:", id);
    }
    static get(id) {
        return this.macros[id];
    }
}
exports.MacroRegistry = MacroRegistry;
MacroRegistry.macros = {};
//# sourceMappingURL=macroRegistry.js.map