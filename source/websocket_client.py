import json
import time
from threading import Thread

import websocket

from operations.config import config
from source.cashbox import CASHBOX
from source.logger import logger
from ui.main_window import (
    service_status_var,
    server_status_label,
    GREEN_LIGHT,
    GREEN_DARK,
    RED_LIGHT,
    RED_DARK,
    cashbox_name_var,
    shift_status_var,
    cashbox_is_connected_var,
)


def on_message(wsapp: websocket.WebSocketApp, message):
    print(message)

    message = json.loads(message)
    try:
        task_number = message["number"]
        del message["number"]
        status, task_data = CASHBOX.send_json_task(message)
        result = {
            "status": "success" if status else "error",
            "number": task_number,
            "data": task_data
        }
        if not CASHBOX.is_connected:
            cashbox_name_var.set(f"Касса не подключена")
            shift_status_var.set(f"Смена - Неизвестно")
            cashbox_is_connected_var.set(False)
    except KeyError:
        result = {
            "status": "error",
            "number": None,
            "data": "bad json received"
        }

    wsapp.send(json.dumps(result))


def on_close(wsapp, *args, **kwargs):
    service_status_var.set(f"Отсутствует cоединение с сервером")
    server_status_label.configure(fg_color=(RED_LIGHT, RED_DARK))
    print("Retry : %s" % time.ctime())
    time.sleep(10)
    connect_websocket()


def on_open(wsapp):
    service_status_var.set(f"Cоединение с сервером установлено")
    server_status_label.configure(fg_color=(GREEN_LIGHT, GREEN_DARK))


def connect_websocket():
    try:
        print("Connecting ws")
        key = config.get("connection_key")
        ws_server = config.get("server")
        debug_log = config.get("net_debug", False)
        websocket.enableTrace(debug_log, logger)
        ws_app = websocket.WebSocketApp(f"ws://{ws_server}/task/{key}", on_message=on_message, on_close=on_close, on_open=on_open)
        wst = Thread(target=ws_app.run_forever, kwargs={
            "ping_timeout": 60,
            "ping_interval": 70
        })
        wst.daemon = True
        wst.start()
        return wst
    except Exception as exp:
        logger.error(exp)





