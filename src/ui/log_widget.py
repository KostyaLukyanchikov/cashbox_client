import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from src.constants import LogLineColor

if TYPE_CHECKING:
    from src.ui.cashbox_widget import CashboxLayout


class LogWidget(QWidget):
    LOG_COLORS = {
        logging.INFO: LogLineColor.GREY,
        logging.WARNING: LogLineColor.ORANGE,
        logging.ERROR: LogLineColor.RED,
    }

    MAX_LOG_LINES = 100  # Максимальное количество строк в текстовом поле

    def __init__(self, parent: "CashboxLayout") -> None:
        super().__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        self.create_logs_section()

    def create_logs_section(self) -> None:
        """Добавляем текстовое поле для логов и кнопку очистки."""
        group_box = QGroupBox(self)
        group_box.setTitle("Логи")
        logs_layout = QVBoxLayout()
        group_box.setLayout(logs_layout)
        self.main_layout.addWidget(group_box)

        self.log_box = QTextEdit(self)
        font = self.log_box.font()
        font.setPointSize(10)  # Устанавливаем размер шрифта
        self.log_box.setFont(font)
        self.log_box.setReadOnly(True)
        logs_layout.addWidget(self.log_box)

        # Добавляем кнопку для очистки логов
        clear_button = QPushButton("Очистить логи", self)
        clear_button.setFixedWidth(120)
        clear_button.clicked.connect(self.clear_logs)
        logs_layout.addWidget(clear_button, alignment=Qt.AlignmentFlag.AlignRight)

    def add_log(
        self, message: str, level: int = 20, exc_info: bool | None = False
    ) -> None:
        """Добавление логов в текстовый бокс с цветом и уровнем"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = self.LOG_COLORS.get(level, LogLineColor.GREY)  # Получаем цвет по уровню

        # Форматируем сообщение
        formatted_message = f"[{timestamp}] [{logging.getLevelName(level)}] {message}"

        # Добавляем сообщение с цветом
        self.log_box.setTextColor(Qt.GlobalColor.white)  # Цвет по умолчанию - белый
        self.log_box.append(f'<span style="color:{color};">{formatted_message}</span>')

        # Проверяем, если строк больше, чем MAX_LOG_LINES, удаляем верхние строки
        if self.log_box.document().blockCount() > self.MAX_LOG_LINES:
            cursor = self.log_box.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        # Записываем лог в файл с пометкой о кассе
        self.log_to_file(message=message, level=level, exc_info=exc_info)

    def log_to_file(
        self, message: str, level: int, exc_info: bool | None = False
    ) -> None:
        """Запись логов в файл с указанием имени кассы"""
        parent: "CashboxLayout" = self.parent()  # type: ignore
        log_message = f"[Касса: {parent.name_edit.text()}]: {message}"
        logging.getLogger().log(level, log_message, exc_info=exc_info)

    def clear_logs(self) -> None:
        """Очищаем лог"""
        self.log_box.clear()


class CashboxLogger:
    def __init__(self, log_widget: LogWidget) -> None:
        self.log_widget = log_widget

    def info(self, msg: str) -> None:
        """Логирование уровня INFO."""
        self.log_widget.add_log(msg, logging.INFO)

    def warning(self, msg: str) -> None:
        """Логирование уровня WARNING."""
        self.log_widget.add_log(msg, logging.WARNING)

    def error(self, msg: str) -> None:
        """Логирование уровня ERROR."""
        self.log_widget.add_log(msg, logging.ERROR)

    def exception(self, msg: str | Exception, exc_info: bool | None = True) -> None:
        """Логирование уровня ERROR."""
        msg = str(msg) if isinstance(msg, Exception) else msg
        self.log_widget.add_log(msg, logging.ERROR, exc_info=exc_info)
