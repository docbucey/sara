"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyStopDeviceListener = void 0;
const vscode = require("vscode");
const deviceListener_1 = require("../devices/deviceListener");
function smithyStopDeviceListener() {
    deviceListener_1.DeviceListener.stop();
    vscode.window.showInformationMessage("Smithy Device Listener stopped.");
}
exports.smithyStopDeviceListener = smithyStopDeviceListener;
//# sourceMappingURL=stopDeviceListener.js.map