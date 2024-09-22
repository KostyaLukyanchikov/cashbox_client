from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMenuBar,
    QPushButton,
    QScrollArea,
)

from src.constants import ColorTheme

if TYPE_CHECKING:
    from src.ui.main_window import MainWindow


class MenuBar(QMenuBar):

    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent=parent)

        self._server_input: QLineEdit | None = None
        self._theme_dropdown: QComboBox | None = None

        self.menu = self.addMenu("Настройки")

        # Добавляем действия
        self.settings_action = QAction("Настройки", self)
        self.settings_action.triggered.connect(self.show_settings_dialog)
        self.about_action = QAction("О программе", self)
        self.about_action.triggered.connect(self.show_about_info)

        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.about_action)

    @property
    def server_input(self) -> QLineEdit:
        if self._server_input is None:
            raise ValueError("server_input is not set")
        return self._server_input

    @server_input.setter
    def server_input(self, value: QLineEdit) -> None:
        self._server_input = value

    @property
    def theme_dropdown(self) -> QComboBox:
        if self._theme_dropdown is None:
            raise ValueError("theme_dropdown is not set")
        return self._theme_dropdown

    @theme_dropdown.setter
    def theme_dropdown(self, value: QComboBox) -> None:
        self._theme_dropdown = value

    def parent(self) -> "MainWindow":
        return super().parent()  # type: ignore

    def show_settings_dialog(self) -> None:
        """Открываем модальное окно для ввода настроек подключения"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")

        layout = QFormLayout(self)

        self.server_input = QLineEdit(self)
        self.server_input.setText(self.parent().config.get("server", ""))
        self.server_input.setFixedWidth(250)
        layout.addRow("Адрес сервера:", self.server_input)

        # Добавляем выбор темы
        theme_label = QLabel("Тема:")
        self.theme_dropdown = QComboBox(self)
        self.theme_dropdown.addItems(["Светлая", "Тёмная", "Системная"])
        theme_map = {
            ColorTheme.LIGHT: "Светлая",
            ColorTheme.DARK: "Тёмная",
            ColorTheme.SYSTEM: "Системная",
        }
        theme_value = theme_map[self.parent().config.get("theme", "Системная")]
        self.theme_dropdown.setCurrentText(theme_value)
        layout.addRow(theme_label, self.theme_dropdown)

        # Кнопка сохранения
        save_button = QPushButton("OK")
        save_button.clicked.connect(lambda: self.accept_dialog(dialog))
        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec()

    def show_about_info(self) -> None:
        """Открываем модальное окно для вывода полезной информации."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Информация")
        dialog.resize(500, 120)

        layout = QGridLayout()

        config_label_name, config_scroll_area = self.create_scrollable_label(
            label_text="Путь до файла конфига:", text=self.parent().config_file_path
        )

        log_label_name, log_scroll_area = self.create_scrollable_label(
            label_text="Путь до файла логов:", text=self.parent().log_file_path
        )

        version_label_name = QLabel("Версия:")
        version_label = QLabel(self)
        version_label.setText("2.0.0")

        layout.addWidget(log_label_name, 0, 0)
        layout.addWidget(log_scroll_area, 0, 1)
        layout.addWidget(config_label_name, 1, 0)
        layout.addWidget(config_scroll_area, 1, 1)
        layout.addWidget(version_label_name, 2, 0)
        layout.addWidget(version_label, 2, 1)

        # Устанавливаем макет и показываем диалог
        dialog.setLayout(layout)
        dialog.exec()

    def accept_dialog(self, dialog: QDialog) -> None:
        server_value = self.server_input.text()
        self.parent().set_server_address(server_value)

        selected_theme = self.theme_dropdown.currentText()
        if selected_theme == "Светлая":
            self.parent().set_theme(ColorTheme.LIGHT)
        elif selected_theme == "Тёмная":
            self.parent().set_theme(ColorTheme.DARK)
        else:
            self.parent().set_theme(ColorTheme.SYSTEM)

        dialog.accept()

    def create_scrollable_label(
        self, label_text: str, text: str
    ) -> tuple[QLabel, QScrollArea]:
        label_name = QLabel(label_text)
        label = QLabel(self)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setText(text)

        scroll_area = QScrollArea(self)
        scroll_area.setWidget(label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        return label_name, scroll_area
