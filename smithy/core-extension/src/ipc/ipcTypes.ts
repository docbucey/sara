export interface SmithyIPCMessage {
    target: "blender" | "sara";
    command: string;
    payload?: any;
}
