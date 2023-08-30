import logging

from customtkinter import *
import pystray
from pystray import MenuItem as item
from PIL import Image

from operations.config import config
from source.cashbox import CASHBOX
from source.logger import logger

global service_status_var

RED_LIGHT = "#FF4B4B"
RED_DARK = "#A42A2A"
GREEN_LIGHT = "#3FD754"
GREEN_DARK = "#2D9E3C"


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.Handler.setFormatter(self, formatter)
        # Store a reference to the Text it will log to
        self.text = text
        self.text.tag_config("INFO", foreground="black")
        self.text.tag_config("DEBUG", foreground="grey")
        self.text.tag_config("WARNING", foreground="orange")
        self.text.tag_config("ERROR", foreground="red")
        self.text.tag_config("CRITICAL", foreground="red", underline=1)

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


def connect_cashbox():
    CASHBOX.setup(WINDOW_HANDLER)
    if CASHBOX.is_connected:
        cashbox_name_var.set(f"{CASHBOX.name}, НОМЕР {CASHBOX.serial_number}")
    else:
        cashbox_name_var.set(f"Касса не подключена")


def open_shift():
    CASHBOX.open_shift()
    shift_status_var.set(f"Смена - {CASHBOX.get_shift_status_caption()}")


def close_shift():
    CASHBOX.close_shift()
    shift_status_var.set(f"Смена - {CASHBOX.get_shift_status_caption()}")


set_default_color_theme("green")
window = CTk()
window.grid_columnconfigure((0, 1), weight=5)
window.title("Кассовый клиент")
window.geometry("800x500")
window.resizable(False, False)

shift_status_var = StringVar()
shift_status_var.set(f"Смена - {CASHBOX.get_shift_status_caption()}")

connection_key_var = StringVar()
connection_key_var.set(config.get("connection_key"))

server_address_var = StringVar()
server_address_var.set(config.get("server"))

cashbox_name_var = StringVar()
cashbox_name_var.set(f"{CASHBOX.name}, НОМЕР {CASHBOX.serial_number}")

service_status_var = StringVar()
service_status_var.set(f"Отсутствует cоединение с сервером")

settings_frame = CTkFrame(window, width=180, height=130)
settings_frame.grid(row=0, column=2, padx=10, pady=(10, 0), columnspan=2,  sticky="nsw")

server_status_label = CTkLabel(window, textvariable=service_status_var, fg_color=(RED_LIGHT, RED_DARK), font=("", 16),  width=320, height=160)
server_status_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nw", columnspan=2)

settings_frame_label = CTkLabel(settings_frame, text="Настройки клиента", font=("", 16),  width=100)
settings_frame_label.grid(row=0, column=0, padx=20, pady=10, sticky="we", columnspan=4)

server_address_label = CTkLabel(settings_frame, text="Адрес сервера", width=100)
server_address_label.grid(row=1, column=0, padx=20, pady=10, sticky="nw", columnspan=1)

server_address_entry = CTkEntry(settings_frame, textvariable=server_address_var, placeholder_text="Адрес сервера", width=280)
server_address_entry.grid(row=1, column=1, padx=20, pady=(10, 10),  sticky="w", columnspan=3)

connection_key_label = CTkLabel(settings_frame, text="Ключ соединения", width=100)
connection_key_label.grid(row=2, column=0, padx=20, pady=10, sticky="nw", columnspan=1)

connection_key_entry = CTkEntry(settings_frame, textvariable=connection_key_var, placeholder_text="Ключ соединения", width=280)
connection_key_entry.grid(row=2, column=1, padx=20, pady=(10, 20), sticky="w", columnspan=3)

cashbox_frame = CTkFrame(window)
cashbox_frame.grid(row=1, column=0, padx=10, pady=(10, 0), columnspan=4,  sticky="nswe")

cashbox_label = CTkLabel(cashbox_frame, textvariable=cashbox_name_var, font=("", 20))
cashbox_label.grid(row=1, column=0, padx=10, pady=10, sticky="w", columnspan=3)

shift_status_label = CTkLabel(cashbox_frame, textvariable=shift_status_var, font=("", 20))
shift_status_label.grid(row=1, column=3, padx=20, pady=10, sticky="w", columnspan=1)

setup_cashbox_button = CTkButton(cashbox_frame, text="Настроить кассу", command=connect_cashbox)
setup_cashbox_button.grid(row=2, column=0, padx=10, pady=10, sticky="w", columnspan=2)


open_shift_button = CTkButton(cashbox_frame, text="Открыть смену", command=open_shift)
open_shift_button.grid(row=4, column=0, padx=10, pady=10, sticky="we")

close_shift_button = CTkButton(cashbox_frame, text="Закрыть смену", command=close_shift)
close_shift_button.grid(row=4, column=1, padx=10, pady=10, sticky="we")

x_report_button = CTkButton(cashbox_frame, text="X-отчет")
x_report_button.grid(row=4, column=2, padx=10, pady=10, sticky="we")

z_report_button = CTkButton(cashbox_frame, text="Z-отчет")
z_report_button.grid(row=4, column=3, padx=10, pady=10, sticky="we")

log_frame = CTkFrame(window)
log_frame.grid(row=2, column=0, padx=10, pady=(10, 0), columnspan=4,  sticky="nswe")

log_label = CTkLabel(log_frame, text="Лог")
log_label.grid(row=0, column=0, padx=5, pady=0, columnspan=4, sticky="w")

log_textbox = CTkTextbox(log_frame, height=100, width=770)
log_textbox.grid(row=1, column=0, padx=5, pady=5, columnspan=4, sticky="we")

text_handler = TextHandler(log_textbox)
logger.addHandler(text_handler)


# Сворачиваем в трей
def quit_window(icon, item):
    icon.stop()
    window.destroy()


def show_window(icon, item):
    icon.stop()
    window.after(0, window.deiconify())


def withdraw_window():
    window.withdraw()
    image = Image.open("icon.ico")
    menu = (item("Настройки", show_window), item("Закрыть программу", quit_window))
    icon = pystray.Icon("name", image, "Кассовый клиент", menu)
    icon.run_detached()


window.protocol('WM_DELETE_WINDOW', withdraw_window)

# window.bind("<Unmap>", withdraw_window)
# window.bind("<Map>", show_window)
#window.iconbitmap("icon.ico")
WINDOW_HANDLER = window.winfo_id()
