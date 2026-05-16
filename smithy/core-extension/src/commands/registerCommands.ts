import { smithyProbeSystem } from './probeSystem';
import { smithyRunInsertCode } from './runInsertCode';
import { smithyOpenProfileEditor } from './openProfileEditor';
import { smithyRegisterMacro } from './registerMacro';
import * as vscode from 'vscode';


import { smithyTestIPC } from './testIPC';
import { smithyStartDeviceListener } from './startDeviceListener';
import { smithyStopDeviceListener } from './stopDeviceListener';

export function registerCommands(context: vscode.ExtensionContext) {
    registerStart(context);
    registerSendToBlender(context);
    registerSendToSara(context);
    registerBindDeviceInput(context);
    registerRunMacro(context);
    registerLoadProfile(context);
    registerSaveProfile(context);

    context.subscriptions.push(
        vscode.commands.registerCommand('smithy.testIPC', smithyTestIPC)
    );
        context.subscriptions.push(
            vscode.commands.registerCommand('smithy.registerMacro', smithyRegisterMacro)
        );
            context.subscriptions.push(
                vscode.commands.registerCommand('smithy.openProfileEditor', smithyOpenProfileEditor)
            );
                context.subscriptions.push(
                    vscode.commands.registerCommand('smithy.insertCodeBlock', smithyRunInsertCode)
                );
                    context.subscriptions.push(
                        vscode.commands.registerCommand('smithy.probeSystem', smithyProbeSystem)
                    );
        context.subscriptions.push(
            vscode.commands.registerCommand('smithy.startDeviceListener', smithyStartDeviceListener)
        );
        context.subscriptions.push(
            vscode.commands.registerCommand('smithy.stopDeviceListener', smithyStopDeviceListener)
        );
}
