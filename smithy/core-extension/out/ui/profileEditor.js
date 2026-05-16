"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProfileEditorPanel = void 0;
const vscode = require("vscode");
const profileManager_1 = require("../profiles/profileManager");
class ProfileEditorPanel {
    static show() {
        if (ProfileEditorPanel.currentPanel) {
            ProfileEditorPanel.currentPanel.panel.reveal();
            return;
        }
        const panel = vscode.window.createWebviewPanel('smithyProfileEditor', 'Smithy Profile Editor', vscode.ViewColumn.One, { enableScripts: true });
        ProfileEditorPanel.currentPanel = new ProfileEditorPanel(panel);
    }
    constructor(panel) {
        this.panel = panel;
        this.panel.webview.html = this.getHtml();
        this.setupMessageHandler();
    }
    setupMessageHandler() {
        this.panel.webview.onDidReceiveMessage(msg => {
            switch (msg.type) {
                case 'load':
                    const profile = profileManager_1.ProfileManager.loadProfile();
                    this.panel.webview.postMessage({ type: 'profile', profile });
                    break;
                case 'save':
                    profileManager_1.ProfileManager.saveProfile(msg.profile);
                    vscode.window.showInformationMessage("Smithy profile saved.");
                    break;
            }
        });
    }
    getHtml() {
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
            < div;
        class {
        }
        "mapping-row";
        style = "margin-bottom: 5px;" >
            class {
            };
        "key";
        value = "${key}";
        placeholder = "Device.Control";
        style = "width: 150px;" >
        ;
        class {
        };
        "val";
        value = "${val}";
        placeholder = "macroId";
        style = "width: 200px;" >
            /div> `;
                }
            </script>
        </body>
        </html>
        `;
    }
}
exports.ProfileEditorPanel = ProfileEditorPanel;
//# sourceMappingURL=profileEditor.js.map