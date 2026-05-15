from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import requests
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


BASE_URL = os.environ.get("SARA_ENVOY_BASE_URL", "http://127.0.0.1:8787")
ENTRYPOINT = os.environ.get("SARA_ENVOY_ENTRYPOINT", "/dashboard")
USERNAME = os.environ.get("SARA_ENVOY_USERNAME", "md")
PASSWORD = os.environ.get("SARA_ENVOY_PASSWORD", "trial-pass-123")
DESKTOP_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_APP_PATH = os.path.join(os.path.dirname(DESKTOP_DIR), "envoy_web", "app.py")


def check_backend(timeout_sec: float = 2.0) -> tuple[bool, str]:
    try:
        r = requests.get(BASE_URL + "/login", timeout=timeout_sec)
        if 200 <= r.status_code < 500:
            return True, f"HTTP {r.status_code}"
        return False, f"unexpected HTTP {r.status_code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def resolve_backend_python() -> tuple[list[str] | None, str]:
    candidates: list[list[str]] = []
    env_python = os.environ.get("SARA_PYTHON_EXE", "").strip()
    if env_python:
        candidates.append([env_python])
    candidates.extend(
        [
            [sys.executable],
            [r"C:\Users\mdbuc\AppData\Local\Python\pythoncore-3.14-64\python.exe"],
            [r"C:\Users\mdbuc\AppData\Local\Programs\Python\Python314\python.exe"],
        ]
    )
    if shutil.which("py"):
        candidates.append(["py", "-3"])
    if shutil.which("python"):
        candidates.append(["python"])

    checked: list[str] = []
    for candidate in candidates:
        exe = candidate[0]
        if os.path.isabs(exe) and not os.path.exists(exe):
            continue
        try:
            probe = subprocess.run(
                [*candidate, "-c", "import flask, requests; print('OK')"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            checked.append(" ".join(candidate))
            if probe.returncode == 0 and "OK" in probe.stdout:
                return candidate, " ".join(candidate)
        except Exception:
            checked.append(" ".join(candidate))

    return None, "; ".join(checked) if checked else "no candidates"


def start_local_backend() -> tuple[subprocess.Popen[str] | None, str]:
    if not os.path.exists(WEB_APP_PATH):
        return None, f"missing backend app: {WEB_APP_PATH}"

    python_cmd, python_detail = resolve_backend_python()
    if python_cmd is None:
        return None, f"no backend-capable Python found: {python_detail}"

    log_dir = os.path.join(DESKTOP_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    stamp = str(int(time.time()))
    out_path = os.path.join(log_dir, f"desktop_backend_{stamp}.out.log")
    err_path = os.path.join(log_dir, f"desktop_backend_{stamp}.err.log")

    env = os.environ.copy()
    env.setdefault("SARA_LOCAL_ONLY", "1")
    env.setdefault("SARA_ENVOY_BASE_URL", BASE_URL)
    env.setdefault("SARA_ENVOY_ENTRYPOINT", ENTRYPOINT)
    env.setdefault("SARA_ENVOY_USERNAME", USERNAME)
    env.setdefault("SARA_ENVOY_PASSWORD", PASSWORD)
    env.setdefault("SARA_ENVOY_SECRET", os.urandom(24).hex())

    out_file = open(out_path, "w", encoding="utf-8")
    err_file = open(err_path, "w", encoding="utf-8")
    try:
        proc = subprocess.Popen(
            [*python_cmd, WEB_APP_PATH],
            cwd=os.path.dirname(WEB_APP_PATH),
            env=env,
            stdout=out_file,
            stderr=err_file,
            text=True,
        )
        out_file.close()
        err_file.close()
    except Exception as e:
        out_file.close()
        err_file.close()
        return None, f"backend spawn failed: {type(e).__name__}: {e}"

    for _ in range(24):
        time.sleep(0.25)
        ok, detail = check_backend(timeout_sec=0.75)
        if ok:
            return proc, f"started local backend via {' '.join(python_cmd)} ({detail})"
        if proc.poll() is not None:
            out_file.close()
            err_file.close()
            err_tail = ""
            if os.path.exists(err_path):
                with open(err_path, "r", encoding="utf-8", errors="ignore") as handle:
                    err_tail = handle.read()[-2000:]
            return None, f"backend exited early: {err_tail or 'see logs'}"

    return None, f"backend did not become ready; logs: {err_path}"


class BrowserPane(QWidget):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self.parent_window = parent
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.toolbar = QToolBar("Browser")
        self.back_btn = QPushButton("<")
        self.forward_btn = QPushButton(">")
        self.reload_btn = QPushButton("Reload")
        self.new_tab_btn = QPushButton("Add Tab")
        self.go_btn = QPushButton("Go")
        self.address = QLineEdit()
        self.address.setPlaceholderText("Enter URL")

        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn.clicked.connect(self.go_forward)
        self.reload_btn.clicked.connect(self.reload_tab)
        self.new_tab_btn.clicked.connect(self.open_blank_tab)
        self.go_btn.clicked.connect(self.navigate_to_address)
        self.address.returnPressed.connect(self.navigate_to_address)

        self.toolbar.addWidget(self.back_btn)
        self.toolbar.addWidget(self.forward_btn)
        self.toolbar.addWidget(self.reload_btn)
        self.toolbar.addWidget(self.new_tab_btn)
        self.toolbar.addWidget(self.address)
        self.toolbar.addWidget(self.go_btn)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        if not ENTRYPOINT.startswith("/"):
            initial = BASE_URL + "/" + ENTRYPOINT
        else:
            initial = BASE_URL + ENTRYPOINT
        self.add_tab(QUrl(initial), "SARA")

    def current_view(self) -> QWebEngineView | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def open_blank_tab(self):
        self.add_tab(QUrl("https://example.com"), "New Tab")

    def add_tab(self, qurl: QUrl, label: str):
        browser = QWebEngineView()
        browser.setUrl(qurl)
        index = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(index)

        browser.urlChanged.connect(lambda u, b=browser: self._on_url_changed(b, u))
        browser.titleChanged.connect(lambda t, b=browser: self._on_title_changed(b, t))

    def close_tab(self, index: int):
        if self.tabs.count() <= 1:
            return
        self.tabs.removeTab(index)

    def _on_url_changed(self, browser: QWebEngineView, url: QUrl):
        if browser == self.current_view():
            self.address.setText(url.toString())

    def _on_title_changed(self, browser: QWebEngineView, title: str):
        i = self.tabs.indexOf(browser)
        if i >= 0:
            self.tabs.setTabText(i, title[:30] if title else "Tab")

    def navigate_to_address(self):
        text = self.address.text().strip()
        if not text:
            return
        parsed = urlparse(text)
        if not parsed.scheme:
            text = "https://" + text
        view = self.current_view()
        if view:
            view.setUrl(QUrl(text))

    def go_back(self):
        view = self.current_view()
        if view:
            view.back()

    def go_forward(self):
        view = self.current_view()
        if view:
            view.forward()

    def reload_tab(self):
        view = self.current_view()
        if view:
            view.reload()


class SaraChatWidget(QWidget):
    def __init__(self, open_profile_callback):
        super().__init__()
        self.open_profile_callback = open_profile_callback
        self.session = requests.Session()

        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Chat setup instruction for SARA")
        self.send_btn = QPushButton("Send")
        self.profile_btn = QPushButton("Server Profile")

        self.send_btn.clicked.connect(self.send_message)
        self.profile_btn.clicked.connect(self.open_profile_callback)
        self.input.returnPressed.connect(self.send_message)

        bottom = QHBoxLayout()
        bottom.addWidget(self.input)
        bottom.addWidget(self.send_btn)
        bottom.addWidget(self.profile_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.transcript)
        layout.addLayout(bottom)
        self.setLayout(layout)
        ok, detail = check_backend()
        if ok:
            self.transcript.append("SARA: Local setup channel ready.")
        else:
            self.transcript.append("SARA: Backend not reachable yet. Start launcher first.")
            self.transcript.append(f"SARA: {detail}")

    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return
        self.transcript.append(f"You: {text}")
        self.input.clear()

        try:
            r = self.session.post(BASE_URL + "/api/chat/setup", json={"message": text}, timeout=10)
            data = r.json()
            if data.get("success"):
                self.transcript.append("SARA: " + str(data.get("reply", "ok")))
            else:
                self.transcript.append("SARA: " + str(data.get("error", "request failed")))
        except Exception as e:
            self.transcript.append(f"SARA: Request failed ({type(e).__name__}).")


class SaraDesktopMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SARA Desktop Browser")
        self.resize(1480, 920)

        self.browser_pane = BrowserPane(self)
        self.setCentralWidget(self.browser_pane)

        self.chat_dock = QDockWidget("SARA Direct Interface", self)
        self.chat_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )
        self.chat_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.chat_widget = SaraChatWidget(self.open_server_profile)
        self.chat_dock.setWidget(self.chat_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.chat_dock)

        # Color theme mapped from your VS Code color set.
        self.setStyleSheet(
            """
            QMainWindow { background: #FFFFFF; color: #002F6C; }
            QDockWidget::title {
                background: #002F6C;
                color: #FFFFFF;
                padding: 6px;
                border-bottom: 2px solid #FFB81C;
            }
            QToolBar {
                background: #F5F5F5;
                border: 1px solid #7A8CA5;
                spacing: 6px;
                padding: 4px;
            }
            QPushButton {
                background: #FFB81C;
                color: #002F6C;
                border: 1px solid #FFB81C;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: 600;
            }
            QPushButton:hover { background: #FFD45A; }
            QLineEdit, QTextEdit {
                background: #FFFFFF;
                color: #002F6C;
                border: 1px solid #7A8CA5;
                border-radius: 5px;
                padding: 4px;
            }
            QTabWidget::pane {
                border: 1px solid #7A8CA5;
                background: #FFFFFF;
            }
            QTabBar::tab {
                background: #F5F5F5;
                color: #002F6C;
                border: 1px solid #7A8CA5;
                border-bottom: none;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #002F6C;
                color: #FFFFFF;
                border-bottom: 2px solid #FFB81C;
            }
            """
        )

    def open_server_profile(self):
        self.browser_pane.add_tab(QUrl(BASE_URL + "/dashboard"), "Server Profile")


def main() -> int:
    app = QApplication(sys.argv)
    backend_proc: subprocess.Popen[str] | None = None
    ok, detail = check_backend()
    if not ok:
        backend_proc, start_detail = start_local_backend()
        ok, detail = check_backend()
        if not ok:
            QMessageBox.critical(
                None,
                "SARA Backend Not Reachable",
                (
                    "Could not connect to the Envoy backend at "
                    f"{BASE_URL}.\n\n"
                    "The desktop app also tried to start the local backend automatically and it still failed.\n\n"
                    f"Initial check: {detail}\n"
                    f"Autostart: {start_detail}"
                ),
            )
            return 2
    win = SaraDesktopMain()
    win.show()
    try:
        return app.exec()
    finally:
        if backend_proc is not None and backend_proc.poll() is None:
            backend_proc.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
