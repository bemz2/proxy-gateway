import json
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk
from urllib.parse import urlencode

import requests
import websocket


API_BASE_URL = os.getenv("PROXY_API_BASE_URL", "http://localhost:8000")


class ProxyDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Proxy Gateway Desktop")
        self.root.configure(bg="#f3f3f3")
        self.style = ttk.Style()

        self.user_id: int | None = None
        self.ws_token: str | None = None
        self.ws: websocket.WebSocketApp | None = None
        self.ws_thread: threading.Thread | None = None
        self.ui_queue: queue.Queue[tuple[str, str, str | None]] = queue.Queue()

        self.activation_key_var = tk.StringVar()
        self.status_var = tk.StringVar(value="ожидание")
        self.status_message_var = tk.StringVar(value="Ключ еще не отправлен.")
        self.host_var = tk.StringVar(value="-")
        self.port_var = tk.StringVar(value="-")
        self.protocol_var = tk.StringVar(value="-")
        self.user_id_var = tk.StringVar(value="-")
        self.message_var = tk.StringVar(value="")
        self.activation_key_entry: tk.Entry | None = None

        self._build_ui()
        self._bind_shortcuts()
        self._fit_window_to_content()
        self._poll_queue()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        self._configure_styles()

        container = tk.Frame(self.root, bg="#f3f3f3", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        panel = tk.Frame(container, bg="#ffffff", bd=1, relief=tk.SOLID)
        panel.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(panel, bg="#ffffff", padx=16, pady=16)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="Подключение к прокси",
            bg="#ffffff",
            fg="#1f1f1f",
            font=("Arial", 16, "bold"),
        )
        title.pack(anchor="w")

        divider = tk.Frame(panel, height=1, bg="#e5e5e5")
        divider.pack(fill=tk.X)

        body = tk.Frame(panel, bg="#ffffff", padx=16, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        key_label = tk.Label(body, text="Ключ активации", bg="#ffffff", anchor="w")
        key_label.pack(fill=tk.X)

        key_entry = tk.Entry(
            body,
            textvariable=self.activation_key_var,
            relief=tk.SOLID,
            bd=1,
            bg="#ffffff",
            fg="#1f1f1f",
            disabledbackground="#f2f2f2",
            disabledforeground="#6a6a6a",
            insertbackground="#1f1f1f",
            selectbackground="#d9e7ff",
            selectforeground="#1f1f1f",
            highlightthickness=0,
        )
        key_entry.pack(fill=tk.X, pady=(8, 0), ipady=8)
        key_entry.bind("<Return>", lambda _: self.connect())
        key_entry.focus_set()
        self.activation_key_entry = key_entry

        button_row = tk.Frame(body, bg="#ffffff")
        button_row.pack(fill=tk.X, pady=(16, 0))

        self.connect_button = ttk.Button(
            button_row,
            text="Подключиться",
            style="Primary.TButton",
            command=self.connect,
        )
        self.connect_button.pack(side=tk.LEFT)

        self.disconnect_button = ttk.Button(
            button_row,
            text="Отключиться",
            style="Secondary.TButton",
            state=tk.DISABLED,
            command=self.disconnect,
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=(8, 0))

        self.message_label = tk.Label(
            body,
            textvariable=self.message_var,
            bg="#ffffff",
            fg="#1f1f1f",
            justify="left",
            wraplength=440,
        )
        self.message_label.pack(fill=tk.X, pady=(16, 0))

        status_frame = tk.Frame(body, bg="#ffffff", pady=16)
        status_frame.pack(fill=tk.X)

        self._add_row(status_frame, "Статус", self.status_var)
        self._add_row(status_frame, "Сообщение", self.status_message_var)

        details_title = tk.Label(
            body,
            text="Данные подключения",
            bg="#ffffff",
            fg="#1f1f1f",
            font=("Arial", 11, "bold"),
        )
        details_title.pack(anchor="w", pady=(8, 8))

        details_frame = tk.Frame(body, bg="#ffffff")
        details_frame.pack(fill=tk.X)

        self._add_row(details_frame, "Host", self.host_var)
        self._add_row(details_frame, "Port", self.port_var)
        self._add_row(details_frame, "Protocol", self.protocol_var)
        self._add_row(details_frame, "User ID", self.user_id_var)

    def _configure_styles(self) -> None:
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure(
            "Primary.TButton",
            font=("Arial", 11),
            padding=(14, 8),
        )
        self.style.map(
            "Primary.TButton",
            foreground=[
                ("disabled", "#8b8b8b"),
                ("!disabled", "#ffffff"),
            ],
            background=[
                ("disabled", "#d6d6d6"),
                ("pressed", "#2b2b2b"),
                ("active", "#2b2b2b"),
                ("!disabled", "#1f1f1f"),
            ],
            bordercolor=[
                ("disabled", "#d6d6d6"),
                ("!disabled", "#1f1f1f"),
            ],
            lightcolor=[
                ("disabled", "#d6d6d6"),
                ("!disabled", "#1f1f1f"),
            ],
            darkcolor=[
                ("disabled", "#d6d6d6"),
                ("!disabled", "#1f1f1f"),
            ],
        )

        self.style.configure(
            "Secondary.TButton",
            font=("Arial", 11),
            padding=(14, 8),
        )
        self.style.map(
            "Secondary.TButton",
            foreground=[
                ("disabled", "#8b8b8b"),
                ("!disabled", "#1f1f1f"),
            ],
            background=[
                ("disabled", "#ececec"),
                ("pressed", "#e5e5e5"),
                ("active", "#e5e5e5"),
                ("!disabled", "#ffffff"),
            ],
            bordercolor=[
                ("disabled", "#d6d6d6"),
                ("!disabled", "#bfbfbf"),
            ],
            lightcolor=[
                ("disabled", "#ececec"),
                ("!disabled", "#ffffff"),
            ],
            darkcolor=[
                ("disabled", "#ececec"),
                ("!disabled", "#ffffff"),
            ],
        )

    def _bind_shortcuts(self) -> None:
        for sequence in (
            "<Control-v>",
            "<Control-V>",
            "<Control-KeyPress-v>",
            "<Control-KeyPress-V>",
            "<Command-v>",
            "<Command-V>",
            "<Command-KeyPress-v>",
            "<Command-KeyPress-V>",
            "<Shift-Insert>",
        ):
            self.root.bind_all(sequence, self._paste_into_focused_widget, add="+")

        for sequence in (
            "<Control-c>",
            "<Control-C>",
            "<Control-KeyPress-c>",
            "<Control-KeyPress-C>",
            "<Command-c>",
            "<Command-C>",
            "<Command-KeyPress-c>",
            "<Command-KeyPress-C>",
        ):
            self.root.bind_all(sequence, self._copy_from_focused_widget, add="+")

        for sequence in (
            "<Control-x>",
            "<Control-X>",
            "<Control-KeyPress-x>",
            "<Control-KeyPress-X>",
            "<Command-x>",
            "<Command-X>",
            "<Command-KeyPress-x>",
            "<Command-KeyPress-X>",
        ):
            self.root.bind_all(sequence, self._cut_from_focused_widget, add="+")

    def _fit_window_to_content(self) -> None:
        self.root.update_idletasks()
        width = max(self.root.winfo_reqwidth(), 500)
        height = self.root.winfo_reqheight()
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(width, height)
        self.root.resizable(False, False)

    def _focused_text_widget(self) -> tk.Widget | None:
        widget = self.root.focus_get()
        return widget if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)) else None

    def _paste_into_focused_widget(self, _event=None) -> str | None:
        widget = self._focused_text_widget()
        if widget is None:
            return None
        try:
            widget.event_generate("<<Paste>>")
            return "break"
        except tk.TclError:
            pass

        try:
            clipboard_text = self.root.clipboard_get()
        except tk.TclError:
            return "break"

        if isinstance(widget, (tk.Entry, ttk.Entry)):
            try:
                selection_start = widget.index("sel.first")
                selection_end = widget.index("sel.last")
                widget.delete(selection_start, selection_end)
                insert_at = selection_start
            except tk.TclError:
                insert_at = widget.index(tk.INSERT)
            widget.insert(insert_at, clipboard_text)
        elif isinstance(widget, tk.Text):
            try:
                widget.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            widget.insert(tk.INSERT, clipboard_text)
        return "break"

    def _copy_from_focused_widget(self, _event=None) -> str | None:
        widget = self._focused_text_widget()
        if widget is None:
            return None
        widget.event_generate("<<Copy>>")
        return "break"

    def _cut_from_focused_widget(self, _event=None) -> str | None:
        widget = self._focused_text_widget()
        if widget is None:
            return None
        widget.event_generate("<<Cut>>")
        return "break"

    def _add_row(self, parent: tk.Widget, label_text: str, value_var: tk.StringVar) -> None:
        row = tk.Frame(parent, bg="#ffffff")
        row.pack(fill=tk.X, pady=4)

        label = tk.Label(row, text=label_text, bg="#ffffff", fg="#5f5f5f", anchor="w")
        label.pack(side=tk.LEFT)

        value = tk.Label(row, textvariable=value_var, bg="#ffffff", fg="#1f1f1f", anchor="e")
        value.pack(side=tk.RIGHT)

    def _poll_queue(self) -> None:
        while not self.ui_queue.empty():
            action, value, extra = self.ui_queue.get()
            if action == "status":
                self.status_var.set(value)
                if extra is not None:
                    self.status_message_var.set(extra)
            elif action == "message":
                self._set_message(value, extra or "info")
            elif action == "vm":
                vm = json.loads(value)
                self.host_var.set(vm.get("host", "-"))
                self.port_var.set(str(vm.get("port", "-")))
                self.protocol_var.set(vm.get("protocol", "-"))
                self.user_id_var.set(extra or "-")
            elif action == "ws_closed":
                self.status_var.set("disconnected")
                self.status_message_var.set("Соединение WebSocket закрыто.")
            elif action == "ws_error":
                self._set_message(value, "error")
        self.root.after(150, self._poll_queue)

    def _set_message(self, text: str, level: str) -> None:
        self.message_var.set(text)
        color = "#1f1f1f"
        if level == "error":
            color = "#7c1f1a"
        elif level == "success":
            color = "#1b5e20"
        self.message_label.configure(fg=color)

    def _set_busy(self, is_busy: bool) -> None:
        self.connect_button.configure(state=tk.DISABLED if is_busy else tk.NORMAL)
        can_disconnect = tk.NORMAL if (not is_busy and self.user_id is not None) else tk.DISABLED
        self.disconnect_button.configure(state=can_disconnect)

    def _clear_vm(self) -> None:
        self.host_var.set("-")
        self.port_var.set("-")
        self.protocol_var.set("-")
        self.user_id_var.set("-")

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
        self.status_var.set("ожидание")
        self.status_message_var.set("Ключ еще не отправлен.")
        self._set_busy(False)

    def connect(self) -> None:
        activation_key = self.activation_key_var.get().strip()
        if not activation_key:
            self._set_message("Введите ключ активации.", "error")
            return

        self._set_busy(True)
        self._set_message("", "info")
        self.status_var.set("ожидание")
        self.status_message_var.set("Отправка ключа на backend.")

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
            vm = data["vm"]

            self.ui_queue.put(("vm", json.dumps(vm), str(self.user_id)))
            self.ui_queue.put(("status", data.get("status", "connected"), data.get("message", "Подключено.")))
            self.ui_queue.put(("message", "Ключ активирован. Подключение установлено.", "success"))
            self.root.after(0, lambda: self._set_busy(False))
            self._open_websocket()
        except Exception as exc:
            self.ui_queue.put(("message", str(exc), "error"))
            self.ui_queue.put(("status", "error", str(exc)))
            self.root.after(0, self._reset_connection)

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
                self.ui_queue.put(("status", payload.get("status", "ожидание"), payload.get("message", "")))
            except json.JSONDecodeError:
                self.ui_queue.put(("message", "Не удалось разобрать сообщение статуса.", "error"))

        def on_error(_, error) -> None:
            self.ui_queue.put(("ws_error", f"Ошибка WebSocket: {error}", None))

        def on_close(*_) -> None:
            self.ui_queue.put(("ws_closed", "", None))

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def disconnect(self) -> None:
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

            self.ui_queue.put(("message", "Подключение закрыто.", "success"))
            self.root.after(0, self._reset_connection)
            self.ui_queue.put(("status", "disconnected", "Прокси освобожден."))
        except Exception as exc:
            self.ui_queue.put(("message", str(exc), "error"))
            self.root.after(0, lambda: self._set_busy(False))

    def on_close(self) -> None:
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
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    ProxyDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
