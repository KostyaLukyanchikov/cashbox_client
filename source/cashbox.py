import json

from lib.libfptr10 import IFptr
from source.logger import logger

open_shift = {
    "type": "openShift",
}
close_shift = {
    "type": "closeShift"
}
x_report = {
    "type": "reportX"
}


class CashBoxClass:
    def __init__(self):
        self.is_connected: bool = False
        self.name = "КАССА НЕ НАСТРОЕНА"
        self.serial_number: str = ""
        self.shift_state: int = -1
        self.__connection: IFptr = IFptr("")
        self.settings: dict = self.__connection.getSettings()
        self.last_error: str = ""

        self.connect()
        self.__populate_cashbox_data()

    def connect(self):
        self.__connection.setSettings(self.settings)
        try:
            res = self.__connection.open()
            if res >= 0:
                self.is_connected = True
        except Exception as exp:
            logger.exception(exp)
            self.is_connected = False

    def __populate_cashbox_data(self):
        if self.is_connected:
            self.__connection.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
            self.__connection.queryData()
            self.serial_number = self.__connection.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
            self.name = self.__connection.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
            self.shift_state = self.__connection.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)

    def setup(self, handler_id: int):
        self.disconnect()
        self.__connection.showProperties(IFptr.LIBFPTR_GUI_PARENT_NATIVE, handler_id)
        self.settings = self.__connection.getSettings()
        self.connect()
        self.__populate_cashbox_data()

    def send_json_task(self, task: dict):
        if not self.is_connected:
            logger.error("CASHBOX IS NOT CONNECTED")
            return False, "CASHBOX IS NOT CONNECTED"
        logger.info(("TASK SENDED", task))
        if not self.__validate_json_task(task):
            return False, self.last_error
        data = json.dumps(task)
        self.__connection.setParam(IFptr.LIBFPTR_PARAM_JSON_DATA, data)
        status = self.__connection.processJson()
        if status < 0:
            return False, self.__get_error()
        res = self.__connection.getParamString(IFptr.LIBFPTR_PARAM_JSON_DATA)
        logger.info(("TASK RESULT", res))
        self.__populate_cashbox_data()

        return True, res

    def __validate_json_task(self, task: dict):
        data = json.dumps(task)
        self.__connection.setParam(IFptr.LIBFPTR_PARAM_JSON_DATA, data)
        if self.__connection.validateJson() < 0:
            self.last_error = f"{self.__connection.errorCode()} {self.__connection.errorDescription()}"
            logger.error(self.last_error)
            return False
        return True

    def __get_error(self):
        error_code = self.__connection.errorCode()
        if error_code in (
                self.__connection.LIBFPTR_ERROR_NO_CONNECTION,
                self.__connection.LIBFPTR_ERROR_PORT_NOT_AVAILABLE,
                self.__connection.LIBFPTR_ERROR_PORT_BUSY,
                self.__connection.LIBFPTR_ERROR_CONNECTION_DISABLED):
            self.disconnect()
        description = self.__connection.errorDescription()
        self.last_error = f"{error_code} {description}"
        logger.error(self.last_error)
        return self.last_error

    def disconnect(self):
        self.__connection.close()
        self.is_connected = False

    def check_connection(self):
        return self.__connection.isOpened()
        self.is_connected = False

    def get_shift_status_caption(self):
        namings = {
            -1: "Неизвестно",
            IFptr.LIBFPTR_SS_CLOSED: "Закрыта",
            IFptr.LIBFPTR_SS_OPENED: "Открыта",
            IFptr.LIBFPTR_SS_EXPIRED: "Истекла"
        }
        return namings[self.shift_state]

    def open_shift(self):
        if self.is_connected:
            self.send_json_task(open_shift)

    def close_shift(self):
        if self.is_connected:
            self.send_json_task(close_shift)

    def x_report(self):
        if self.is_connected:
            self.send_json_task(x_report)


CASHBOX = CashBoxClass()
