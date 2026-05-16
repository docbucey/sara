import * as vscode from 'vscode';
import { ProfileEditorPanel } from '../ui/profileEditor';

export function smithyOpenProfileEditor() {
    ProfileEditorPanel.show();
}
