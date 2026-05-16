export function sendToSara(action: string, payload: any = {}) {
    console.log("[Smithy] SARA Bridge →", action, payload);
    // IPC/WebSocket placeholder
    IPCClient.send({
        target: "sara",
        command: action,
        payload
    });
