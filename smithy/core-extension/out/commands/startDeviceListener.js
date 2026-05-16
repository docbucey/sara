"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyStartDeviceListener = void 0;
const vscode = require("vscode");
const deviceListener_1 = require("../devices/deviceListener");
function smithyStartDeviceListener() {
    deviceListener_1.DeviceListener.start();
    vscode.window.showInformationMessage("Smithy Device Listener started.");
}
exports.smithyStartDeviceListener = smithyStartDeviceListener;
//# sourceMappingURL=startDeviceListener.js.map