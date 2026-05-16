"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.simulateHOTASInput = exports.handleHOTASInput = void 0;
// HOTAS device handler stub
function handleHOTASInput(event) {
    // Normalize and process HOTAS input event
}
exports.handleHOTASInput = handleHOTASInput;
const deviceListener_1 = require("./deviceListener");
function simulateHOTASInput(control, value = 1) {
    deviceListener_1.DeviceListener.handleRawInput({
        device: "HOTAS",
        control,
        value
    });
}
exports.simulateHOTASInput = simulateHOTASInput;
// HOTAS device handler stub
function handleHOTASInput(event) {
    // Normalize and process HOTAS input event
}
exports.handleHOTASInput = handleHOTASInput;
//# sourceMappingURL=hotas.js.map