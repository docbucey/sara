"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.smithyInsertCodeBlock = void 0;
const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
function smithyInsertCodeBlock(filePath, code) {
    var _a;
    return __awaiter(this, void 0, void 0, function* () {
        const workspace = (_a = vscode.workspace.workspaceFolders) === null || _a === void 0 ? void 0 : _a[0];
        if (!workspace) {
            vscode.window.showErrorMessage("Smithy: No workspace open.");
            return;
        }
        const fullPath = path.join(workspace.uri.fsPath, filePath);
        // Ensure folder exists
        const dir = path.dirname(fullPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        // Create file if missing
        if (!fs.existsSync(fullPath)) {
            fs.writeFileSync(fullPath, "");
        }
        // Open the file in VS Code
        const doc = yield vscode.workspace.openTextDocument(fullPath);
        const editor = yield vscode.window.showTextDocument(doc);
        // Insert code at end of file
        const lastLine = doc.lineCount;
        const position = new vscode.Position(lastLine, 0);
        yield editor.edit(editBuilder => {
            editBuilder.insert(position, "\n" + code + "\n");
        });
        vscode.window.showInformationMessage(`Smithy: Code inserted into ${filePath}`);
    });
}
exports.smithyInsertCodeBlock = smithyInsertCodeBlock;
//# sourceMappingURL=insertCodeBlock.js.map