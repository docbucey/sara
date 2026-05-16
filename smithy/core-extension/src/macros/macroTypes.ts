export interface SmithyMacro {
    id: string;
    action: string;      // e.g. "sendToBlender:extrude"
    payload?: any;       // optional data
}
