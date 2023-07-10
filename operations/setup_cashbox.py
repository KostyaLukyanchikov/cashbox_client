from tkinter import *

from source.cashbox import CASHBOX
from ui.main_window import WINDOW_HANDLER


def connect_cashbox():
    CASHBOX.setup(WINDOW_HANDLER)

