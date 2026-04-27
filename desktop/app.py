import json
import os
import re
import sys
import threading
from urllib.parse import urlencode

import requests
import websocket
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget


API_BASE_URL = os.getenv("PROXY_API_BASE_URL", "http://localhost:8000")


def normalize_activation_key(raw_key: str) -> str:
    collapsed = re.sub(r"[\s\u200b\u200c\u200d\ufeff]+", "", raw_key).lower()
    match = re.search(r"([0-9a-f]{32})", collapsed)
    return match.group(1) if match else collapsed


class UiBridge(QObject):
    status_changed = pyqtSignal(str, str)
    message_changed = pyqtSignal(str, str)
    vm_changed = pyqtSignal(dict, str)
    connection_reset = pyqtSignal()
    busy_changed = pyqtSignal(bool)
    clear_key_requested = pyqtSignal()


class ProxyDesktopApp(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.user_id: int | None = None
        self.ws_token: str | None = None
        self.ws: websocket.WebSocketApp | None = None
        self.ws_thread: threading.Thread | None = None

        self.bridge = UiBridge()
        self.bridge.status_changed.connect(self._handle_status_changed)
        self.bridge.message_changed.connect(self._handle_message_changed)
        self.bridge.vm_changed.connect(self._handle_vm_changed)
        self.bridge.connection_reset.connect(self._reset_connection)
        self.bridge.busy_changed.connect(self._set_busy)
        self.bridge.clear_key_requested.connect(self.activation_key_entry_clear)

        self._build_ui()
        self._reset_connection()

    def _build_ui(self) -> None:
        self.setWindowTitle("Proxy Gateway Desktop")
        self.setMinimumWidth(520)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(0)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        root_layout.addWidget(panel)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(0)

        title = QLabel("Подключение к прокси")
        title.setObjectName("title")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        panel_layout.addWidget(header)

        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        panel_layout.addWidget(divider)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(16)
        panel_layout.addWidget(body)

        key_label = QLabel("Ключ активации")
        body_layout.addWidget(key_label)

        self.activation_key_entry = QLineEdit()
        self.activation_key_entry.setPlaceholderText("Вставьте ключ активации")
        self.activation_key_entry.returnPressed.connect(self.connect_proxy)
        body_layout.addWidget(self.activation_key_entry)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        body_layout.addLayout(button_row)

        self.connect_button = QPushButton("Подключиться")
        self.connect_button.setObjectName("primaryButton")
        self.connect_button.clicked.connect(self.connect_proxy)
        button_row.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Отключиться")
        self.disconnect_button.clicked.connect(self.disconnect_proxy)
        button_row.addWidget(self.disconnect_button)
        button_row.addStretch(1)

        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        body_layout.addWidget(self.message_label)

        self.status_value_label = QLabel("")
        self.status_message_label = QLabel("")
        self.status_message_label.setWordWrap(True)
        self.host_value_label = QLabel("-")
        self.port_value_label = QLabel("-")
        self.protocol_value_label = QLabel("-")
        self.user_id_value_label = QLabel("-")

        status_grid = QGridLayout()
        status_grid.setHorizontalSpacing(12)
        status_grid.setVerticalSpacing(8)
        status_grid.setContentsMargins(0, 0, 0, 0)
        body_layout.addLayout(status_grid)

        self._add_row(status_grid, 0, "Статус", self.status_value_label)
        self._add_row(status_grid, 1, "Сообщение", self.status_message_label)

        details_title = QLabel("Данные подключения")
        details_title.setObjectName("sectionTitle")
        details_font = QFont()
        details_font.setPointSize(11)
        details_font.setBold(True)
        details_title.setFont(details_font)
        body_layout.addWidget(details_title)

        details_grid = QGridLayout()
        details_grid.setHorizontalSpacing(12)
        details_grid.setVerticalSpacing(8)
        details_grid.setContentsMargins(0, 0, 0, 0)
        body_layout.addLayout(details_grid)

        self._add_row(details_grid, 0, "Host", self.host_value_label)
        self._add_row(details_grid, 1, "Port", self.port_value_label)
        self._add_row(details_grid, 2, "Protocol", self.protocol_value_label)
        self._add_row(details_grid, 3, "User ID", self.user_id_value_label)

        self.setStyleSheet(
            """
            QWidget {
                background: #f3f3f3;
                color: #1f1f1f;
                font-size: 13px;
            }
            QFrame#panel {
                background: #ffffff;
                border: 1px solid #d7d7d7;
            }
            QLabel#title {
                background: #ffffff;
                color: #1f1f1f;
            }
            QLabel#sectionTitle {
                color: #1f1f1f;
            }
            QFrame#divider {
                background: #e5e5e5;
                border: none;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cfcfcf;
                border-radius: 6px;
                padding: 10px 12px;
                selection-background-color: #d9e7ff;
            }
            QLineEdit:disabled {
                background: #f2f2f2;
                color: #6a6a6a;
            }
            QPushButton {
                border: 1px solid #bfbfbf;
                border-radius: 6px;
                padding: 8px 14px;
                background: #ffffff;
            }
            QPushButton#primaryButton {
                background: #1f1f1f;
                color: #ffffff;
                border-color: #1f1f1f;
            }
            QPushButton:disabled {
                color: #8b8b8b;
                background: #ececec;
                border-color: #d6d6d6;
            }
            """
        )

        self.activation_key_entry.setFocus()

    def _add_row(self, layout: QGridLayout, row: int, label_text: str, value_label: QLabel) -> None:
        label = QLabel(label_text)
        label.setStyleSheet("color: #5f5f5f;")
        value_label.setWordWrap(True)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label, row, 0)
        layout.addWidget(value_label, row, 1)

    def _set_busy(self, is_busy: bool) -> None:
        is_connected = self.user_id is not None
        self.connect_button.setDisabled(is_busy or is_connected)
        self.disconnect_button.setDisabled(is_busy or not is_connected)
        self.activation_key_entry.setDisabled(is_connected)

    def _clear_vm(self) -> None:
        self.host_value_label.setText("-")
        self.port_value_label.setText("-")
        self.protocol_value_label.setText("-")
        self.user_id_value_label.setText("-")

    def _reset_connection(self) -> None:
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None
        self.user_id = None
        self.ws_token = None
        self._clear_vm()
        self._handle_status_changed("ожидание", "Ключ еще не отправлен.")
        self._set_busy(False)

    def _handle_status_changed(self, status_text: str, message: str) -> None:
        self.status_value_label.setText(status_text)
        self.status_message_label.setText(message)

    def _handle_message_changed(self, text: str, level: str) -> None:
        color = "#1f1f1f"
        if level == "error":
            color = "#7c1f1a"
        elif level == "success":
            color = "#1b5e20"
        self.message_label.setStyleSheet(f"color: {color};")
        self.message_label.setText(text)

    def _handle_vm_changed(self, vm: dict, user_id: str) -> None:
        self.host_value_label.setText(str(vm.get("host", "-")))
        self.port_value_label.setText(str(vm.get("port", "-")))
        self.protocol_value_label.setText(str(vm.get("protocol", "-")))
        self.user_id_value_label.setText(user_id or "-")

    def activation_key_entry_clear(self) -> None:
        self.activation_key_entry.clear()

    def connect_proxy(self) -> None:
        activation_key = normalize_activation_key(self.activation_key_entry.text())
        if not activation_key:
            self._handle_message_changed("Введите ключ активации.", "error")
            return

        self._set_busy(True)
        self._handle_message_changed("", "info")
        self._handle_status_changed("ожидание", "Отправка ключа на backend.")

        thread = threading.Thread(target=self._connect_worker, args=(activation_key,), daemon=True)
        thread.start()

    def _connect_worker(self, activation_key: str) -> None:
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/proxy/activate-key",
                json={"activation_key": activation_key},
                timeout=15,
            )
            data = response.json()
            if not response.ok:
                raise RuntimeError(data.get("detail") or "Не удалось активировать ключ.")

            self.user_id = data["user_id"]
            self.ws_token = data["ws_token"]
            self.bridge.vm_changed.emit(data["vm"], str(self.user_id))
            self.bridge.status_changed.emit(
                data.get("status", "connected"),
                data.get("message", "Подключено."),
            )
            self.bridge.message_changed.emit("Ключ активирован. Подключение установлено.", "success")
            self.bridge.busy_changed.emit(False)
            self.bridge.clear_key_requested.emit()
            self._open_websocket()
        except Exception as exc:
            self.bridge.message_changed.emit(str(exc), "error")
            self.bridge.status_changed.emit("error", str(exc))
            self.bridge.connection_reset.emit()

    def _open_websocket(self) -> None:
        if self.user_id is None or self.ws_token is None:
            return

        params = urlencode({"token": self.ws_token})
        if API_BASE_URL.startswith("https://"):
            ws_base = API_BASE_URL.replace("https://", "wss://", 1)
        else:
            ws_base = API_BASE_URL.replace("http://", "ws://", 1)

        ws_url = f"{ws_base}/api/ws/status/{self.user_id}?{params}"

        def on_message(_, message: str) -> None:
            try:
                payload = json.loads(message)
                self.bridge.status_changed.emit(
                    payload.get("status", "ожидание"),
                    payload.get("message", ""),
                )
            except json.JSONDecodeError:
                self.bridge.message_changed.emit(
                    "Не удалось разобрать сообщение статуса.",
                    "error",
                )

        def on_error(_, error) -> None:
            self.bridge.message_changed.emit(f"Ошибка WebSocket: {error}", "error")

        def on_close(*_) -> None:
            self.bridge.status_changed.emit("disconnected", "Соединение WebSocket закрыто.")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def disconnect_proxy(self) -> None:
        if self.user_id is None:
            return

        self._set_busy(True)
        thread = threading.Thread(target=self._disconnect_worker, args=(self.user_id,), daemon=True)
        thread.start()

    def _disconnect_worker(self, user_id: int) -> None:
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/proxy/disconnect",
                json={"user_id": user_id},
                timeout=15,
            )
            data = response.json()
            if not response.ok:
                raise RuntimeError(data.get("detail") or "Не удалось отключиться.")

            self.bridge.message_changed.emit("Подключение закрыто.", "success")
            self.bridge.connection_reset.emit()
            self.bridge.status_changed.emit("disconnected", "Прокси освобожден.")
        except Exception as exc:
            self.bridge.message_changed.emit(str(exc), "error")
            self.bridge.busy_changed.emit(False)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.user_id is not None:
            try:
                requests.post(
                    f"{API_BASE_URL}/api/proxy/disconnect",
                    json={"user_id": self.user_id},
                    timeout=3,
                )
            except Exception:
                pass
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    window = ProxyDesktopApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
