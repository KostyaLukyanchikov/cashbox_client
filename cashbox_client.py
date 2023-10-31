from operations.config import collect_config
from source.websocket_client import connect_websocket
from ui.main_window import window, WINDOW_HANDLER
from source.logger import logger

global win_id


if __name__ == '__main__':
    try:
        ws_thread = connect_websocket()
    except Exception as exp:
        logger.error(exp)
    window.mainloop()
    ws_thread.join()
