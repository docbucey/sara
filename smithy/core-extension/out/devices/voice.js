"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleVoiceInput = exports.simulateVoiceInput = void 0;
// Voice device handler stub
const deviceListener_1 = require("./deviceListener");
function simulateVoiceInput(phrase) {
    deviceListener_1.DeviceListener.handleRawInput({
        device: "Voice",
        control: "Phrase",
        value: phrase
    });
}
exports.simulateVoiceInput = simulateVoiceInput;
function handleVoiceInput(event) {
    // Normalize and process voice input event
}
exports.handleVoiceInput = handleVoiceInput;
//# sourceMappingURL=voice.js.map