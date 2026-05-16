"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MacroEngine = void 0;
const blenderBridge_1 = require("../bridges/blenderBridge");
const saraBridge_1 = require("../bridges/saraBridge");
class MacroEngine {
    static run(macro) {
        console.log("[Smithy] Running macro:", macro);
        const [target, command] = macro.action.split(":");
        switch (target) {
            case "blender":
                (0, blenderBridge_1.sendToBlender)(command, macro.payload);
                break;
            case "sara":
                (0, saraBridge_1.sendToSara)(command, macro.payload);
                break;
            default:
                console.warn("[Smithy] Unknown macro target:", target);
        }
    }
}
exports.MacroEngine = MacroEngine;
//# sourceMappingURL=macroEngine.js.map