import json
import time
from threading import Thread

import websocket

from operations.config import config
from source.cashbox import CASHBOX
from source.logger import logger
from ui.main_window import service_status_var, server_status_label, GREEN_LIGHT, GREEN_DARK, RED_LIGHT, RED_DARK


def on_message(wsapp: websocket.WebSocketApp, message):
    print(message)

    message = json.loads(message)
    try:
        task_number = message["number"]
        del message["number"]
        status, task_data = CASHBOX.send_json_task(message)
        print("RESULT")
        result = {
            "status": "success" if status else "error",
            "number": task_number,
            "data": task_data
        }
    except KeyError:
        result = {
            "status": "error",
            "number": None,
            "data": None
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
    print("Connecting ws")
    key = config.get("connection_key")
    ws_server = config.get("server")
    websocket.enableTrace(False, logger)
    ws_app = websocket.WebSocketApp(f"ws://{ws_server}/task/{key}", on_message=on_message, on_close=on_close, on_open=on_open)
    wst = Thread(target=ws_app.run_forever)
    wst.daemon = True
    wst.start()
    return wst





