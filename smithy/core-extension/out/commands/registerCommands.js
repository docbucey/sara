"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerCommands = void 0;
const probeSystem_1 = require("./probeSystem");
const runInsertCode_1 = require("./runInsertCode");
const openProfileEditor_1 = require("./openProfileEditor");
const registerMacro_1 = require("./registerMacro");
const vscode = require("vscode");
const testIPC_1 = require("./testIPC");
const startDeviceListener_1 = require("./startDeviceListener");
const stopDeviceListener_1 = require("./stopDeviceListener");
function registerCommands(context) {
    registerStart(context);
    registerSendToBlender(context);
    registerSendToSara(context);
    registerBindDeviceInput(context);
    registerRunMacro(context);
    registerLoadProfile(context);
    registerSaveProfile(context);
    context.subscriptions.push(vscode.commands.registerCommand('smithy.testIPC', testIPC_1.smithyTestIPC));
    context.subscriptions.push(vscode.commands.registerCommand('smithy.registerMacro', registerMacro_1.smithyRegisterMacro));
    context.subscriptions.push(vscode.commands.registerCommand('smithy.openProfileEditor', openProfileEditor_1.smithyOpenProfileEditor));
    context.subscriptions.push(vscode.commands.registerCommand('smithy.insertCodeBlock', runInsertCode_1.smithyRunInsertCode));
    context.subscriptions.push(vscode.commands.registerCommand('smithy.probeSystem', probeSystem_1.smithyProbeSystem));
    context.subscriptions.push(vscode.commands.registerCommand('smithy.startDeviceListener', startDeviceListener_1.smithyStartDeviceListener));
    context.subscriptions.push(vscode.commands.registerCommand('smithy.stopDeviceListener', stopDeviceListener_1.smithyStopDeviceListener));
}
exports.registerCommands = registerCommands;
//# sourceMappingURL=registerCommands.js.map