import { SmithyMacro } from "./macroTypes";

export class MacroRegistry {
    private static macros: Record<string, SmithyMacro> = {};

    static register(id: string, macro: SmithyMacro) {
        this.macros[id] = macro;
        console.log("[Smithy] Macro registered:", id);
    }

    static get(id: string): SmithyMacro | undefined {
        return this.macros[id];
    }
}
