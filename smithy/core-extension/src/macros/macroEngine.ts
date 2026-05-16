import { SmithyMacro } from "./macroTypes";
import { sendToBlender } from "../bridges/blenderBridge";
import { sendToSara } from "../bridges/saraBridge";

export class MacroEngine {
    static run(macro: SmithyMacro) {
        console.log("[Smithy] Running macro:", macro);

        const [target, command] = macro.action.split(":");

        switch (target) {
            case "blender":
                sendToBlender(command, macro.payload);
                break;

            case "sara":
                sendToSara(command, macro.payload);
                break;

            default:
                console.warn("[Smithy] Unknown macro target:", target);
        }
    }
}
