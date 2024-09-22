import json
import logging
from copy import copy
from dataclasses import dataclass
from typing import Any

from lib.libfptr10 import IFptr
from src import errors
from src.ui.log_widget import CashboxLogger

open_shift = {
    "type": "openShift",
}
close_shift = {"type": "closeShift"}
x_report = {"type": "reportX"}


@dataclass
class CashBoxDriverError:
    code: int
    description: str

    def __str__(self) -> str:
        return f"Код: {self.code}, Описание: {self.description}"


class Cashbox:
    def __init__(
        self,
        model: str,
        serial_number: str,
        port: str,
        settings: dict[str, Any],
    ):
        self.model = model
        self.serial_number = serial_number
        self.port = port
        self.settings = settings
        self.is_connected: bool = False
        self.shift_state: int = -1
        self.last_error: CashBoxDriverError | None = None
        self.__connection: IFptr | None = None
        self._logger: CashboxLogger | logging.Logger | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cashbox):
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return hash(self.serial_number)

    @property
    def _connection(self) -> IFptr:
        if self.__connection is None:
            raise ValueError("_connection is not set")
        return self.__connection

    @_connection.setter
    def _connection(self, value: IFptr) -> None:
        self.__connection = value

    @property
    def logger(self) -> CashboxLogger | logging.Logger:
        return self._logger or logging.getLogger(__name__)

    @logger.setter
    def logger(self, logger: CashboxLogger) -> None:
        self._logger = logger

    @property
    def name(self) -> str:
        return f"{self.model} {self.serial_number}"

    def connect(self) -> None:
        self._connection = IFptr()  # type: ignore
        self._connection.setSettings(self.settings)  # type: ignore
        res = self._connection.open()  # type: ignore
        if res >= 0:
            self.is_connected = True
        else:
            self.is_connected = False
            raise errors.CashboxConnectionError(
                f"Не удалось установить связь с кассой: {self.name}"
            )
        self._update_shift_state()

    def _update_shift_state(self) -> None:
        if not self.is_connected:
            self.shift_state = -1
            return

        self._connection.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)  # type: ignore
        self._connection.queryData()  # type: ignore
        self.shift_state = self._connection.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)  # type: ignore

    def send_json_task(self, task: dict[str, Any]) -> str:
        self.logger.info(f"Получена задача: {task}")

        try:
            res = self._execute_json_task(task)
        finally:
            self._update_shift_state()

        return res

    def _execute_json_task(self, task: dict[str, Any]) -> str:
        if not self.is_connected:
            raise errors.CashboxConnectionError(
                "Задача не может быть выполнена: Касса не подключена к устройству"
            )

        if not self._validate_json_task(task):
            raise errors.CashboxTaskError(
                f"Задача не может быть выполнена: {str(self.last_error)}"
            )

        data = json.dumps(task)
        self._connection.setParam(IFptr.LIBFPTR_PARAM_JSON_DATA, data)  # type: ignore
        status = self._connection.processJson()  # type: ignore

        if status >= 0:
            res = self._connection.getParamString(IFptr.LIBFPTR_PARAM_JSON_DATA)  # type: ignore
            self.logger.info(f"Результат выполнения: {res}")
            return str(res)

        error = self._get_error()
        if error.code in (
            self._connection.LIBFPTR_ERROR_NO_CONNECTION,
            self._connection.LIBFPTR_ERROR_PORT_NOT_AVAILABLE,
            self._connection.LIBFPTR_ERROR_PORT_BUSY,
            self._connection.LIBFPTR_ERROR_CONNECTION_DISABLED,
        ):
            raise errors.CashboxConnectionError(
                "Задача не может быть выполнена: Касса не подключена к устройству"
            )
        else:
            raise errors.CashboxTaskError(
                f"Ошибка при выполнении задачи: {str(self._get_error())}"
            )

    def _validate_json_task(self, task: dict[str, Any]) -> bool:
        to_validate = True
        valid = False

        if task["type"] == "getDeviceStatus":
            # cause `validateJson` on `getDeviceStatus` returns `LIBFPTR_ERROR_VALIDATE_FUNC_NOT_FOUND`
            to_validate = False
            valid = True

        if to_validate:
            data = json.dumps(task)
            self._connection.setParam(IFptr.LIBFPTR_PARAM_JSON_DATA, data)  # type: ignore
            if self._connection.validateJson() < 0:  # type: ignore
                self.last_error = CashBoxDriverError(
                    code=self._connection.errorCode(),  # type: ignore
                    description=self._connection.errorDescription(),  # type: ignore
                )
                self.logger.error(str(self.last_error))
            else:
                valid = True

        return valid

    def _get_error(self) -> CashBoxDriverError:
        self.last_error = CashBoxDriverError(
            code=self._connection.errorCode(),  # type: ignore
            description=self._connection.errorDescription(),  # type: ignore
        )
        return self.last_error

    def disconnect(self) -> None:
        self._connection.close()  # type: ignore
        self.is_connected = False

    def check_connection(self) -> int:
        return self._connection.isOpened()  # type: ignore

    def get_shift_status_caption(self) -> str:
        namings = {
            -1: "Неизвестно",
            IFptr.LIBFPTR_SS_CLOSED: "Закрыта",
            IFptr.LIBFPTR_SS_OPENED: "Открыта",
            IFptr.LIBFPTR_SS_EXPIRED: "Истекла",
        }
        return namings[self.shift_state]

    def open_shift(self) -> None:
        self.send_json_task(open_shift)

    def close_shift(self) -> None:
        self.send_json_task(close_shift)

    def x_report(self) -> None:
        self.send_json_task(x_report)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Cashbox":
        return Cashbox(
            model=value["model"],
            serial_number=value["serial_number"],
            port=value["port"],
            settings=value["settings"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "serial_number": self.serial_number,
            "port": self.port,
            "settings": self.settings,
        }


class CashboxManager:
    _all_cashboxes: set[Cashbox] = set()  # Множество всех найденных касс
    _used_cashboxes: dict[str, Cashbox] = {}  # Для хранения привязанных касс

    @classmethod
    def search_for_cashboxes(cls) -> list[Cashbox]:
        """Ищет все доступные кассы и обновляет внутренний список"""
        found_cashboxes = []

        base_settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,
            IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200,
        }

        possible_ports = [
            f"COM{i}" for i in range(1, 21)
        ]  # Перебираем все возможные COM-порты

        for port in possible_ports:
            settings = copy(base_settings)
            settings[IFptr.LIBFPTR_SETTING_COM_FILE] = port  # type: ignore

            try:
                fptr = IFptr()  # type: ignore
                fptr.setSettings(settings)  # type: ignore
                if fptr.open() == 0:  # type: ignore
                    fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)  # type: ignore
                    fptr.queryData()  # type: ignore

                    cb = Cashbox(
                        model=fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME),  # type: ignore
                        serial_number=fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER),  # type: ignore
                        port=port,
                        settings=fptr.getSettings(),  # type: ignore
                    )
                    found_cashboxes.append(cb)
                    fptr.close()  # type: ignore
            except Exception as e:
                raise errors.CashboxConnectionError(str(e)) from e

        # Обновляем список касс и удаляем из назначенных те, что больше не найдены
        cls._all_cashboxes = cls._all_cashboxes | set(found_cashboxes)

        return found_cashboxes

    @classmethod
    def get_available_cashboxes(cls) -> list[Cashbox]:
        """Возвращаем список доступных касс, которые еще не привязаны к вкладкам."""
        return [
            cb
            for cb in cls._all_cashboxes
            if cb.serial_number not in cls._used_cashboxes
        ]

    @staticmethod
    def is_cashbox_selected(serial_number: str) -> bool:
        return serial_number in CashboxManager._used_cashboxes

    @classmethod
    def acquire_cashbox(cls, cashbox: Cashbox) -> Cashbox:
        if cashbox not in cls._all_cashboxes:
            cls._all_cashboxes.add(cashbox)

        if cashbox.serial_number in CashboxManager._used_cashboxes:
            raise errors.CashboxAlreadyInUse(
                f"Касса с номером {cashbox.serial_number} уже используется."
            )

        try:
            cashbox.connect()
        except Exception as e:
            cashbox.is_connected = False
            cls._all_cashboxes.remove(cashbox)
            cls._used_cashboxes.pop(cashbox.serial_number, None)
            raise errors.CashboxConnectionError(str(e)) from e

        cls._used_cashboxes[cashbox.serial_number] = cashbox
        return cashbox

    @classmethod
    def release_cashbox(cls, serial_number: str) -> None:
        """Освобождаем кассу с указанным серийным номером, чтобы ее можно было использовать в других вкладках."""
        cashbox = None
        for cb in cls._all_cashboxes:
            if cb.serial_number == serial_number:
                cashbox = cb
                break

        if not cashbox:
            return

        try:
            cashbox.disconnect()
            del CashboxManager._used_cashboxes[serial_number]
        except Exception as e:
            raise errors.CashboxDisconnectionError(str(e)) from e


if __name__ == "__main__":
    CashboxManager.search_for_cashboxes()
    cashboxes = CashboxManager.get_available_cashboxes()
    print(cashboxes)
