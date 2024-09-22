import json
import logging
import logging.handlers
import os
import sys
from typing import Any, cast

import darkdetect
from PySide6.QtGui import QCloseEvent, QColor, QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from src.cashbox import Cashbox, CashboxManager
from src.constants import ColorTheme
from src.ui.cashbox_widget import CashboxLayout
from src.ui.menu_widget import MenuBar
from src.ui.tab_widget import TabWidget


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.app = app
        self.resize(700, 600)
        self.app.setStyle("Fusion")
        self.setWindowTitle("Cashbox")

        # Создаем экземпляр менеджера касс
        self.cashbox_manager = CashboxManager()

        # Настраиваем конфиги
        self._data_dir = self._get_data_dir_path()
        self.config_file_path = os.path.join(self._data_dir, "config.json")
        self.log_file_path = os.path.join(self._data_dir, "cashbox_client.log")
        self.config = self._load_config()
        self.setup_logging()

        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Виджет вкладок
        self.tab_widget = TabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # Загружаем состояние приложения при запуске
        loaded = self.load_state()
        if not loaded:
            self.tab_widget.add_tab()
        self.tab_widget.add_plus_tab()

        # Подключаем сигнал для сохранения состояния при закрытии приложения
        self.closeEvent = self.save_state_on_close  # type: ignore

        self.set_theme(self.config.get("theme", ColorTheme.SYSTEM))

    @staticmethod
    def _get_data_dir_path() -> str:
        app_data_dir = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
        cashbox_data_dir = os.path.join(app_data_dir, "CashboxClient")

        if not os.path.exists(cashbox_data_dir):
            os.makedirs(cashbox_data_dir)

        return cashbox_data_dir

    def _load_config(self) -> dict[str, Any]:
        if not os.path.exists(self.config_file_path):
            return {}

        with open(self.config_file_path) as file:
            try:
                return json.load(file)  # type: ignore
            except json.JSONDecodeError as e:
                msg = "Парсинг конфиг файла не удался."
                QMessageBox.warning(self, "Ошибка", msg)
                logging.exception(f"{msg}: {e}", exc_info=True)
                sys.exit(0)

    def setup_logging(self) -> None:
        """Настройка глобального логера для записи логов в файл"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    filename=self.log_file_path,
                    maxBytes=1048576 * 5,  # 5 MB
                    backupCount=7,
                    encoding="utf-8",
                ),
                logging.StreamHandler(),
            ],
        )

    def save_state(self) -> None:
        """Сохраняем текущее состояние приложения в файл config.json"""
        state = {
            "server": self.config.get("server", ""),  # Сохраняем адрес сервера
            "theme": self.config.get("theme", ColorTheme.SYSTEM),  # Сохраняем тему
            "tabs": [],
        }

        # Сохраняем состояние всех вкладок
        for i in range(self.tab_widget.count() - 1):  # Игнорируем вкладку "+"
            tab = self.tab_widget.widget(i)
            tab = cast(CashboxLayout, tab)
            state["tabs"].append(
                {
                    "name": tab.name_edit.text(),
                    "key": tab.key_edit.text(),
                    "cashbox": tab.cashbox.to_dict() if tab.cashbox else None,
                }
            )

        # Сохраняем в файл
        with open(self.config_file_path, "w") as file:
            json.dump(state, file, indent=4, ensure_ascii=False)

    def load_state(self) -> bool:
        """Загружаем состояние приложения из конфига"""
        if not self.config:
            return False

        # Восстанавливаем вкладки
        tabs = self.config.get("tabs", [])
        if not tabs:
            self.tab_widget.add_tab()
        for tab_info in tabs:
            self.tab_widget.add_tab(
                name=tab_info.get("name", "Новая касса"),
                key=tab_info.get("key", ""),
                cashbox=(
                    Cashbox.from_dict(tab_info["cashbox"])
                    if tab_info.get("cashbox")
                    else None
                ),
            )

        return True

    def save_state_on_close(self, event: QCloseEvent) -> None:
        """Сохраняем состояние при закрытии окна"""
        self.save_state()
        event.accept()

    def set_theme(self, theme: str) -> None:
        """Устанавливает тему приложения"""
        if theme == ColorTheme.DARK:
            self.apply_dark_theme()
        elif theme == ColorTheme.LIGHT:
            self.apply_light_theme()
        else:
            self.apply_system_theme()  # для значения 'system'

        # Сохраняем выбор пользователя в конфиг
        self.config["theme"] = theme
        self.save_state()

    def set_server_address(self, address: str) -> None:
        """Устанавливает тему приложения"""
        # Сохраняем значение в конфиг
        self.config["server"] = address
        self.save_state()

    def apply_dark_theme(self) -> None:
        """Применяет темную тему"""
        palette = QPalette()

        # Настраиваем все доступные роли для темной темы
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Shadow, QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.Light, QColor(70, 70, 70))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.Dark, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Mid, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(128, 128, 128))
        palette.setColor(QPalette.ColorRole.Accent, QColor(42, 130, 218))

        # Применяем палитру ко всему приложению
        self.app.setPalette(palette)

        # Убедимся, что диалоговые окна наследуют эту палитру
        QApplication.setPalette(palette)

    def apply_light_theme(self) -> None:
        """Применяет светлую тему"""
        palette = QPalette()

        # Настраиваем все доступные роли для светлой темы
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Shadow, QColor(160, 160, 160))
        palette.setColor(QPalette.ColorRole.Light, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(210, 210, 210))
        palette.setColor(QPalette.ColorRole.Dark, QColor(190, 190, 190))
        palette.setColor(QPalette.ColorRole.Mid, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(128, 128, 128))
        palette.setColor(QPalette.ColorRole.Accent, QColor(0, 120, 215))

        self.app.setPalette(palette)

    def apply_system_theme(self) -> None:
        """Применяет тему, настроенную в системе"""
        theme = ColorTheme.LIGHT if darkdetect.isLight() else ColorTheme.DARK
        self.set_theme(theme)
