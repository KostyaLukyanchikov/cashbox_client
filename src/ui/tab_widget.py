from typing import Any, cast

from PySide6.QtWidgets import QTabWidget, QWidget

from src.cashbox import Cashbox
from src.ui.cashbox_widget import CashboxLayout


class TabWidget(QTabWidget):
    TAB_DEFAULT_NAME: str = "Новая касса"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Обрабатываем нажатие на вкладки
        self.tabBarClicked.connect(self.handle_tab_click)

        # Добавляем возможность закрывать вкладки
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)

    def add_plus_tab(self) -> None:
        """Добавление вкладки '+' для создания новых вкладок"""
        plus_tab = QWidget(self)
        self.addTab(plus_tab, "+")

    def add_tab(
        self,
        name: str | None = None,
        key: str | None = None,
        cashbox: Cashbox | None = None,
        append: bool = True,
    ) -> None:
        """Добавление новой вкладки с именем и ключом"""
        # Если нет имени, задаем дефолтное значение
        name = name or self.TAB_DEFAULT_NAME

        # Создаем новый виджет вкладки
        cashbox_layout = CashboxLayout(
            parent=self, name=name, connection_key=key or "", cashbox=cashbox
        )

        # Добавляем страницу с вкладкой
        if append:
            insert_idx = self.count()
        else:
            insert_idx = self.count() - 1

        index = self.insertTab(
            insert_idx, cashbox_layout, cashbox_layout.name_edit.text()
        )

        # Связываем изменение текста с обновлением названия вкладки
        cashbox_layout.name_edit.textChanged.connect(
            lambda: self.update_tab_name(index, cashbox_layout)
        )

    def update_tab_name(self, index: int, layout: CashboxLayout) -> None:
        """Обновление названия вкладки при изменении текста"""
        self.setTabText(index, layout.name_edit.text())

    def handle_tab_click(self, index: int) -> None:
        """Обрабатываем нажатие на вкладку"""
        if self.tabText(index) == "+":
            self.add_new_tab()

    def add_new_tab(self) -> None:
        """Создание новой вкладки с дефолтным именем 'Касса N'"""
        self.add_tab(append=False)

    def close_tab(self, close_index: int) -> None:
        """Закрытие вкладки"""
        if self.tabText(close_index) == "+":  # Не даем закрыть вкладку "+"
            return

        tab = self.widget(close_index)
        tab = cast(CashboxLayout, tab)
        tab.destroy()

        self.removeTab(close_index)

        # После удаления вкладки, активной делаем ту, что была перед ней или оставляем текущуюю
        curr_selected_index = self.currentIndex()
        if curr_selected_index != close_index:
            return

        new_active_index = close_index - 1 if close_index > 0 else 0
        self.setCurrentIndex(new_active_index)
