import * as vscode from 'vscode';
import { ProfileManager } from '../profiles/profileManager';

export class ProfileEditorPanel {
    public static currentPanel: ProfileEditorPanel | undefined;
    private readonly panel: vscode.WebviewPanel;

    static show() {
        if (ProfileEditorPanel.currentPanel) {
            ProfileEditorPanel.currentPanel.panel.reveal();
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'smithyProfileEditor',
            'Smithy Profile Editor',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        ProfileEditorPanel.currentPanel = new ProfileEditorPanel(panel);
    }

    private constructor(panel: vscode.WebviewPanel) {
        this.panel = panel;

        this.panel.webview.html = this.getHtml();
        this.setupMessageHandler();
    }

    private setupMessageHandler() {
        this.panel.webview.onDidReceiveMessage(msg => {
            switch (msg.type) {
                case 'load':
                    const profile = ProfileManager.loadProfile();
                    this.panel.webview.postMessage({ type: 'profile', profile });
                    break;

                case 'save':
                    ProfileManager.saveProfile(msg.profile);
                    vscode.window.showInformationMessage("Smithy profile saved.");
                    break;
            }
        });
    }

    private getHtml(): string {
        return `
        <!DOCTYPE html>
        <html>
        <body style="font-family: sans-serif; padding: 10px;">
            <h2>Smithy Profile Editor</h2>

            <button onclick="loadProfile()">Load Profile</button>
            <button onclick="saveProfile()">Save Profile</button>

            <h3>Mappings</h3>
            <div id="mappings"></div>

            <script>
                const vscode = acquireVsCodeApi();

                function loadProfile() {
                    vscode.postMessage({ type: 'load' });
                }

                function saveProfile() {
                    const rows = document.querySelectorAll('.mapping-row');
                    const mappings = {};

                    rows.forEach(row => {
                        const key = row.querySelector('.key').value;
                        const val = row.querySelector('.val').value;
                        if (key && val) mappings[key] = val;
                    });

                    vscode.postMessage({
                        type: 'save',
                        profile: { name: "default", mappings }
                    });
                }

                window.addEventListener('message', event => {
                    const msg = event.data;

                    if (msg.type === 'profile') {
                        const container = document.getElementById('mappings');
                        container.innerHTML = '';

                        for (const key in msg.profile.mappings) {
                            container.innerHTML += rowHtml(key, msg.profile.mappings[key]);
                        }

                        container.innerHTML += rowHtml('', '');
                    }
                });

                function rowHtml(key, val) {
                    return `
                        <div class="mapping-row" style="margin-bottom: 5px;">
                            <input class="key" value="${key}" placeholder="Device.Control" style="width: 150px;">
                            →
                            <input class="val" value="${val}" placeholder="macroId" style="width: 200px;">
                        </div>
                    `;
                }
            </script>
        </body>
        </html>
        `;
    }
}
