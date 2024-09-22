import json
from collections.abc import Callable
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from logging import Logger
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QEvent, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src import errors
from src.cashbox import Cashbox, CashboxManager
from src.errors import CashboxConnectionError
from src.ui.log_widget import CashboxLogger, LogWidget
from src.ws_client import WebSocketClient

if TYPE_CHECKING:
    from src.ui.main_window import MainWindow
    from src.ui.tab_widget import TabWidget


class CashboxLayout(QWidget):
    # Создаем сигналы для передачи данных в основной поток
    connection_open_signal = Signal()
    connection_close_signal = Signal(str)
    connection_error_signal = Signal(str)

    def __init__(
        self,
        parent: "TabWidget",
        name: str,
        connection_key: str,
        cashbox: Cashbox | None,
    ):
        super().__init__()

        self.tab_widget = parent
        self.cashbox: Cashbox | None = None
        self.websocket_client: WebSocketClient | None = None
        self._logger: CashboxLogger | Logger | None = None
        self.thread_executor = ThreadPoolExecutor(max_workers=5)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.create_info_section(name)
        self.create_server_section(connection_key)
        self.create_buttons_section()
        self.create_logs_section()

        # Подключаем сигналы к соответствующим слотам
        self.connection_error_signal.connect(self.on_error_received)
        self.connection_close_signal.connect(self.on_close_received)
        self.connection_open_signal.connect(self.on_connection_open)

        # Таймер на подключение и переподключение к серверу
        self.retry_delay: int = 10
        self.retry_timer = QTimer(self)
        self.retry_timer.setInterval(self.retry_delay * 1000)
        self.retry_timer.timeout.connect(self.try_connect_to_server)

        # Автоматически пытаемся подключиться к кассе
        self.attach_cashbox(cashbox)

        # Автоматически пытаемся подключиться при старте
        self.try_connect_to_server()

    @property
    def logger(self) -> CashboxLogger | Logger:
        if self._logger is None:
            raise ValueError("_logger is not set")
        return self._logger

    @logger.setter
    def logger(self, value: CashboxLogger | Logger) -> None:
        self._logger = value

    @property
    def server_address(self) -> str:
        main_window: "MainWindow" = self.tab_widget.parent()  # type: ignore
        return str(main_window.config.get("server", ""))

    @property
    def connection_key(self) -> str:
        return self.key_edit.text()

    @property
    def connection_address(self) -> str:
        return f"ws://{self.server_address}/task/{self.connection_key}"

    def create_info_section(self, name: str) -> None:
        info_group_box = QGroupBox(self)
        info_group_box.setTitle("Информация о кассе")
        info_layout = QHBoxLayout()
        info_group_box.setLayout(info_layout)
        self.main_layout.addWidget(info_group_box)

        self.name_edit = QLineEdit(name, self)
        self.cashbox_info = QLabel("Касса: НЕИЗВЕСТНО", self)
        self.shift_status = QLabel("Смена: НЕИЗВЕСТНО", self)

        separator1 = QLabel("|", self)
        separator1.setStyleSheet("color: gray;")
        separator2 = QLabel("|", self)
        separator2.setStyleSheet("color: gray;")

        info_layout.addWidget(QLabel("Название:"))
        info_layout.addWidget(self.name_edit)
        info_layout.addWidget(separator1)
        info_layout.addWidget(self.cashbox_info)
        info_layout.addWidget(separator2)
        info_layout.addWidget(self.shift_status)

    def create_server_section(self, connection_key: str) -> None:
        """Создаем секцию с информацией о сервере и статусом соединения"""
        conn_group_box = QGroupBox(self)
        conn_group_box.setTitle("Сведение о сервере")
        conn_layout = QHBoxLayout()
        conn_group_box.setLayout(conn_layout)
        self.main_layout.addWidget(conn_group_box)

        self.key_edit = QLineEdit(connection_key, self)
        self.key_edit.setFixedWidth(270)
        connection_label = QLabel("Соединение с сервером:")
        self.connection_indicator = ConnectionIndicator(self)
        separator1 = QLabel("|", self)
        separator1.setStyleSheet("color: gray;")

        conn_layout.addWidget(QLabel("Ключ соединения:"))
        conn_layout.addWidget(self.key_edit)
        conn_layout.addWidget(separator1)
        conn_layout.addWidget(connection_label)
        conn_layout.addWidget(self.connection_indicator)

    def schedule_reconnect(self) -> None:
        """Запускаем таймер повторного подключения, если подключение не удалось."""
        self.logger.info(
            f"Попытка повторного подключения через {self.retry_delay} секунд..."
        )
        if self.retry_timer.isActive():
            return
        self.retry_timer.start()

    def try_connect_to_server(self) -> None:
        """Пробуем подключиться к серверу."""
        if self.websocket_client and self.websocket_client.connected:
            self.logger.info("Клиент уже подключен к серверу")
            self.retry_timer.stop()  # Останавливаем таймер, если уже подключены
            return

        if not self.server_address:
            self.logger.warning("Не указан адрес сервера в настройках")
            self.schedule_reconnect()
            return

        if not self.connection_key:
            self.logger.warning("Не указан ключ соединения")
            self.schedule_reconnect()
            return

        # Пробуем подключиться
        self.connect_to_server()

    def connect_to_server(self) -> None:
        """Открываем WebSocket соединение в фоне"""
        try:
            # Создаем экземпляр WebSocketClient
            self.websocket_client = WebSocketClient(
                server_address=self.connection_address,
                on_message_callback=self.on_message_received,
                on_open_callback=self.connection_open_signal.emit,
                on_error_callback=self.connection_error_signal.emit,
                on_close_callback=self.connection_close_signal.emit,
                logger=self.logger,
            )

            # Подключаемся к серверу
            self.websocket_client.connect()

        except Exception as e:
            self.logger.error(f"Ошибка при подключении к серверу: {str(e)}")
            self.schedule_reconnect()

    def on_connection_open(self) -> None:
        """Обработка события подключения к серверу"""
        self.connection_indicator.set_connected(True)
        self.logger.info(f"Подключено к серверу {self.server_address}")
        self.retry_timer.stop()  # Останавливаем таймер, так как соединение установлено

    def on_message_received(self, message: str) -> None:
        """Обработка сообщения от сервера"""
        task_number = None

        try:
            task = json.loads(message)
            task_number = task["number"]
            del task["number"]
            result = {
                "status": "success",
                "number": task_number,
                "data": self.cashbox.send_json_task(task),  # type: ignore
            }
        except (json.JSONDecodeError, KeyError):
            self.logger.exception("Невалидный формат задачи")
            result = {
                "status": "error",
                "number": task_number,
                "data": "Bad json received",
            }
        except errors.CashboxClientError as e:
            self.logger.exception(e)
            result = {"status": "error", "number": task_number, "data": str(e)}
        except Exception as e:
            self.logger.exception("Непредвиденная ошибка во время выполнения задачи")
            result = {"status": "error", "number": task_number, "data": str(e)}
        finally:
            self._update_cashbox_info()

        self.websocket_client.send(json.dumps(result, ensure_ascii=False))  # type: ignore

    def on_error_received(self, message: str) -> None:
        """Обработка ошибки соединения"""
        if not self.websocket_client:
            return

        self.logger.error(f"Ошибка соединения с сервером: {message}")
        self._close_connection()
        self.schedule_reconnect()  # Планируем повторное подключение

    def on_close_received(self, message: str) -> None:
        """Обработка потери соединения"""
        if not self.websocket_client:
            return

        self.logger.error(f"Соединение с сервером потеряно: {message}")
        self._close_connection()
        self.schedule_reconnect()  # Планируем повторное подключение

    def _close_connection(self) -> None:
        """Закрываем текущее соединение"""
        if self.websocket_client:
            try:
                self.websocket_client.close()
            except Exception as e:
                self.logger.error(f"Ошибка при закрытии соединения: {str(e)}")
            self.connection_indicator.set_connected(False)
            self.websocket_client = None

    def create_buttons_section(self) -> None:
        self.setup_button = QPushButton(parent=self, text="Настроить")
        self.setup_button.clicked.connect(self.open_cashbox_selection_dialog)

        self.open_button = QPushButton(parent=self, text="Открыть смену")
        self.open_button.clicked.connect(self.open_shift)  # Привязка метода

        self.close_button = QPushButton(parent=self, text="Закрыть смену")
        self.close_button.clicked.connect(self.close_shift)  # Привязка метода

        self.report_button = QPushButton(parent=self, text="X-отчет")
        self.report_button.clicked.connect(self.x_report)  # Привязка метода

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.setup_button)
        buttons_layout.addWidget(self.open_button)
        buttons_layout.addWidget(self.close_button)
        buttons_layout.addWidget(self.report_button)

        group_box = QGroupBox(self)
        group_box.setTitle("Действия с кассой")
        group_box.setLayout(buttons_layout)

        # Добавляем секцию кнопок в основной макет
        self.main_layout.addWidget(group_box)

    def open_cashbox_selection_dialog(self) -> None:
        """Открывает диалоговое окно для выбора кассы"""
        dialog = CashboxSelectionDialog(self)
        if dialog.exec():
            selected_cashbox = dialog.get_selected_cashbox()
            self.connect_to_cashbox(selected_cashbox)

    def connect_to_cashbox(self, cashbox: Cashbox | None) -> None:
        """Открывает диалоговое окно для выбора кассы"""
        if cashbox is None:
            self.logger.warning("Касса не выбрана.")
            return

        self.attach_cashbox(cashbox)

    def attach_cashbox(self, cashbox: Cashbox | None) -> None:
        """Привязывает кассу к текущему виджету и обновляет UI"""
        if not cashbox:
            self.logger.warning("Касса не задана для текущей вкладки")
            return

        if self.cashbox:
            if self.cashbox.serial_number == cashbox.serial_number:
                return
            # Освобождаем текущую кассу, если есть
            self.detach_cashbox()

        # Проверяем, не привязана ли касса к другому виджету
        if CashboxManager.is_cashbox_selected(cashbox.serial_number):
            QMessageBox.warning(
                self, "Ошибка", "Эта касса уже используется в другой вкладке."
            )
            return

        # Создаем объект кассы и подключаемся
        try:
            self.cashbox = CashboxManager.acquire_cashbox(cashbox)
            self.cashbox.logger = self.logger
            self.logger.info(f"Касса {self.cashbox.name} привязана.")
        except Exception as e:
            self.logger.error(msg=str(e))

        self._update_cashbox_info()

    def detach_cashbox(self) -> None:
        """Отвязываем кассу от текущей вкладки."""
        if not self.cashbox:
            return

        try:
            CashboxManager.release_cashbox(self.cashbox.serial_number)
            self.logger.info(f"Касса {self.cashbox.name} отвязана.")
        except Exception as e:
            self.logger.error(msg=str(e))

        self.cashbox = None
        self._update_cashbox_info()

    def open_shift(self) -> None:
        """Открывает смену на кассе"""
        if not self.cashbox:
            self.logger.warning("Нет подключенной кассы")
            return

        self._execute_cashbox_method(self.cashbox.open_shift)
        self._update_cashbox_info()

    def close_shift(self) -> None:
        """Закрывает смену на кассе"""
        if not self.cashbox:
            self.logger.warning("Нет подключенной кассы")
            return

        self._execute_cashbox_method(self.cashbox.close_shift)
        self._update_cashbox_info()

    def x_report(self) -> None:
        """Печатает X-отчет на кассе"""
        if not self.cashbox:
            self.logger.warning("Нет подключенной кассы")
            return

        self._execute_cashbox_method(self.cashbox.x_report)

    def _execute_cashbox_method(
        self, method: Callable[[], Any], *args: Any, **kwargs: Any
    ) -> None:
        future = self.thread_executor.submit(method, *args, **kwargs)
        future.add_done_callback(self._task_callback)

    def _task_callback(self, future: Future[Any]) -> Any:
        try:
            return future.result()
        except CashboxConnectionError as e:
            self.logger.error(msg=str(e))
            self.detach_cashbox()
        except Exception as e:
            self.logger.error(msg=str(e))

    def _update_cashbox_info(self) -> None:
        """Обновляет информацию о привязанной кассе"""
        if not self.cashbox:
            self.cashbox_info.setText("Касса: НЕИЗВЕСТНО")
            self.shift_status.setText("Смена: НЕИЗВЕСТНО")
        else:
            self.cashbox_info.setText(f"Касса: {self.cashbox.name}")
            self.shift_status.setText(
                f"Смена: {self.cashbox.get_shift_status_caption()}"
            )

    def create_logs_section(self) -> None:
        """Добавляем виджет логов."""
        log_widget = LogWidget(self)
        self.logger = CashboxLogger(log_widget)
        self.main_layout.addWidget(log_widget)

    def destroy(self, *args: Any, **kwargs: Any) -> None:
        self.detach_cashbox()
        self._close_connection()
        super().destroy(*args, *kwargs)


class ConnectionIndicator(QWidget):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.connected = False  # Начальный статус (отключено)
        self.setFixedSize(20, 20)  # Размер индикатора

        # Устанавливаем начальную подсказку
        self.update_tooltip()

    def paintEvent(self, event: QEvent) -> None:
        """Отрисовка индикатора (круг)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Выбираем цвет в зависимости от статуса подключения
        color = QColor(0, 255, 0) if self.connected else QColor(255, 0, 0)

        # Рисуем круг с выбранным цветом
        painter.setBrush(QBrush(color))
        painter.drawEllipse(0, 0, self.width(), self.height())

    def set_connected(self, status: bool) -> None:
        """Метод для изменения статуса подключения"""
        self.connected = status
        self.update_tooltip()  # Обновляем текст подсказки
        self.update()  # Перерисовываем виджет

    def update_tooltip(self) -> None:
        """Обновление текста подсказки"""
        status_text = "Есть соединение" if self.connected else "Нет соединения"
        self.setToolTip(status_text)

    def enterEvent(self, event: QEvent) -> None:
        """Обрабатываем наведение мыши на индикатор"""
        self.update_tooltip()  # Обновляем текст при наведении


class CashboxSelectionDialog(QDialog):
    def __init__(self, parent: CashboxLayout) -> None:
        super().__init__(parent)
        self.setMinimumWidth(400)
        self.setMinimumHeight(100)
        self.setWindowTitle("Выбор кассы")

        # Основной макет
        layout = QVBoxLayout(self)

        # Область поиска
        search_layout = QHBoxLayout()
        # Выпадающий список для выбора кассы
        self.combo_box = QComboBox(self)
        self.combo_box.addItem("Выберите кассу...")
        # Инициализация комбо бокса
        self.update_combo_box()
        search_layout.addWidget(self.combo_box)
        # Кнопка для запуска поиска касс
        self.search_button = QPushButton("Обнаружить кассы", self)
        self.search_button.clicked.connect(self.start_search)
        search_layout.addWidget(self.search_button)

        # Прогресс бар для индикации процесса поиска касс
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(
            0, 0
        )  # Устанавливаем режим неопределенного прогресса
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Кнопка привязки и отвязки кассы
        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Привязать кассу", self)
        self.detach_button = QPushButton("Отключить кассу", self)

        self.attach_button.clicked.connect(self.accept)
        self.detach_button.clicked.connect(self.detach)

        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.detach_button)

        layout.addLayout(search_layout)
        layout.addLayout(button_layout)

        # Инициализируем поток для поиска касс
        self.search_thread = CashboxSearchThread()
        self.search_thread.finished.connect(self.on_search_finished)

    def start_search(self) -> None:
        """Запускаем поиск касс в отдельном потоке."""
        self.search_button.setEnabled(False)  # Отключаем кнопку поиска
        self.progress_bar.setVisible(True)  # Отображаем прогресс бар
        self.search_thread.start()  # Запускаем поток

    def on_search_finished(self) -> None:
        """Обработка завершения поиска касс."""
        self.update_combo_box()  # Обновляем выпадающий список касс
        self.progress_bar.setVisible(False)  # Скрываем прогресс бар
        self.search_button.setEnabled(True)  # Включаем кнопку поиска

    def update_combo_box(self) -> None:
        self.combo_box.clear()
        self.combo_box.addItem("Выберите кассу...")  # Дефолтное значение
        for cashbox in CashboxManager.get_available_cashboxes():
            self.combo_box.addItem(f"{cashbox.name}", cashbox)

        parent_cashbox = self.parent().cashbox  # type: ignore
        if parent_cashbox is None:
            return

        idx = self.combo_box.findText(parent_cashbox.name)
        if idx < 0:
            idx = 1
            self.combo_box.insertItem(idx, f"{parent_cashbox.name}", parent_cashbox)

        self.combo_box.setCurrentIndex(idx)

    def get_selected_cashbox(self) -> Cashbox | None:
        selected_index = self.combo_box.currentIndex()
        return self.combo_box.currentData() if selected_index >= 0 else None

    def detach(self) -> None:
        parent: CashboxLayout = self.parent()  # type: ignore
        parent.detach_cashbox()
        self.combo_box.setCurrentIndex(0)


class CashboxSearchThread(QThread):
    """Поток для поиска касс."""

    def run(self) -> None:
        CashboxManager.search_for_cashboxes()
