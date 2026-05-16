"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.normalizeInput = void 0;
function normalizeInput(raw) {
    var _a;
    return {
        device: raw.device || "unknown",
        control: raw.control || "unknown",
        value: (_a = raw.value) !== null && _a !== void 0 ? _a : 0
    };
}
exports.normalizeInput = normalizeInput;
//# sourceMappingURL=inputNormalizer.js.map