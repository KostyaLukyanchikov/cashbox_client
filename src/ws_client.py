import threading
from collections.abc import Callable
from logging import Logger
from typing import Any

import websocket

from src.errors import NotConnectedToServer
from src.ui.log_widget import CashboxLogger


class WebSocketClient:
    def __init__(
        self,
        server_address: str,
        on_message_callback: Callable[[Any], Any],
        on_open_callback: Callable[[], Any],
        on_error_callback: Callable[[str], Any],
        on_close_callback: Callable[[str], Any],
        logger: CashboxLogger | Logger,
    ) -> None:
        self.server_address = server_address
        self.connected = False

        self.__ws: websocket.WebSocketApp | None = None
        self.__ws_thread: threading.Thread | None = None
        self._on_message_callback = on_message_callback
        self._on_open_callback = on_open_callback
        self._on_error_callback = on_error_callback
        self._on_close_callback = on_close_callback

        self.logger = logger

    @property
    def _ws(self) -> websocket.WebSocketApp:
        if self.__ws is None:
            raise ValueError("_ws is not set")
        return self.__ws

    @_ws.setter
    def _ws(self, value: websocket.WebSocketApp) -> None:
        self.__ws = value

    @property
    def _ws_thread(self) -> threading.Thread:
        if self.__ws_thread is None:
            raise ValueError("_ws_thread is not set")
        return self.__ws_thread

    @_ws_thread.setter
    def _ws_thread(self, value: threading.Thread) -> None:
        self.__ws_thread = value

    def connect(self) -> None:
        """Открываем WebSocket соединение в отдельном потоке"""
        if self.connected:
            return

        self._ws = websocket.WebSocketApp(
            self.server_address,
            on_open=self.on_open,
            on_message=self.on_message,
            on_close=self.on_close,
            on_error=self.on_error,
        )

        self._ws_thread = threading.Thread(target=self.run_forever, daemon=True)
        self._ws_thread.start()

    def run_forever(self) -> None:
        """Запускаем WebSocket с обработкой ошибок и безопасным завершением"""
        try:
            self._ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            self.on_error(self._ws.sock, str(e))

    def on_open(self, ws: websocket.WebSocket) -> None:
        """Вызывается при получении сообщения от сервера"""
        self.connected = True
        self._on_open_callback()

    def on_message(self, ws: websocket.WebSocket, message: Any) -> None:
        """Вызывается при получении сообщения от сервера"""
        self._on_message_callback(message)

    def on_close(
        self, ws: websocket.WebSocket, close_status_code: int, close_msg: str
    ) -> None:
        """Вызывается при закрытии соединения"""
        self.connected = False
        self._on_close_callback(f"code: {close_status_code}, reason: {close_msg}")

    def on_error(self, ws: websocket.WebSocket | None, err_msg: Any) -> None:
        """Обработка ошибки при соединении"""
        self.connected = False
        self._on_error_callback(str(err_msg))

    def close(self) -> None:
        """Закрываем соединение и безопасно завершаем поток"""
        try:
            if self._ws:
                self._ws.close()
        except Exception as e:
            self.logger.exception(f"Ошибка при закрытии WebSocket: {e}")

        try:
            if self._ws_thread:
                self._ws_thread.join()
        except Exception as e:
            self.logger.error(f"Ошибка при завершении потока с WebSocket: {e}")

        self.connected = False

    def send(self, message: str) -> None:
        if not self.connected:
            raise NotConnectedToServer("Нет подключения к серверу")

        self._ws.send(message.encode("utf-8"))
