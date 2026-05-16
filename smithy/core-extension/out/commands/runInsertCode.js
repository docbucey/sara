"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyRunInsertCode = void 0;
const vscode = require("vscode");
const insertCodeBlock_1 = require("./insertCodeBlock");
function smithyRunInsertCode() {
    vscode.window.showInputBox({
        prompt: "Enter file path (relative to workspace)"
    }).then(filePath => {
        if (!filePath)
            return;
        vscode.window.showInputBox({
            prompt: "Paste the code block to insert"
        }).then(code => {
            if (!code)
                return;
            (0, insertCodeBlock_1.smithyInsertCodeBlock)(filePath, code);
        });
    });
}
exports.smithyRunInsertCode = smithyRunInsertCode;
//# sourceMappingURL=runInsertCode.js.map