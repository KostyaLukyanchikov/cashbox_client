from operations.config import collect_config
from source.websocket_client import connect_websocket
from ui.main_window import window, WINDOW_HANDLER

global win_id


if __name__ == '__main__':
    connect_websocket()
    window.mainloop()
