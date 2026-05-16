import * as vscode from 'vscode';
import { DeviceListener } from '../devices/deviceListener';

export function smithyStopDeviceListener() {
    DeviceListener.stop();
    vscode.window.showInformationMessage("Smithy Device Listener stopped.");
}
