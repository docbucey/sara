"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.simulateG13Input = exports.handleG13Input = void 0;
// G13 device handler stub
function handleG13Input(event) {
    // Normalize and process G13 input event
}
exports.handleG13Input = handleG13Input;
const deviceListener_1 = require("./deviceListener");
function simulateG13Input(control, value = 1) {
    deviceListener_1.DeviceListener.handleRawInput({
        device: "G13",
        control,
        value
    });
}
exports.simulateG13Input = simulateG13Input;
// G13 device handler stub
function handleG13Input(event) {
    // Normalize and process G13 input event
}
exports.handleG13Input = handleG13Input;
//# sourceMappingURL=g13.js.map