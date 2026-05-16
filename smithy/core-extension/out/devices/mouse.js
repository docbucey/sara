"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleMouseInput = exports.simulateMouseInput = void 0;
// Mouse device handler stub
const deviceListener_1 = require("./deviceListener");
function simulateMouseInput(control, value = 1) {
    deviceListener_1.DeviceListener.handleRawInput({
        device: "Mouse",
        control,
        value
    });
}
exports.simulateMouseInput = simulateMouseInput;
// Mouse device handler stub
function handleMouseInput(event) {
    // Normalize and process mouse input event
}
exports.handleMouseInput = handleMouseInput;
//# sourceMappingURL=mouse.js.map