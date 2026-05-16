import * as vscode from 'vscode';
import { DeviceListener } from '../devices/deviceListener';

export function smithyStartDeviceListener() {
    DeviceListener.start();
    vscode.window.showInformationMessage("Smithy Device Listener started.");
}
