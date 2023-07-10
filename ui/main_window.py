from tkinter import *
from source.cashbox import CASHBOX

global service_status_var

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


window = Tk()
window.title("CashBox client")
window.geometry("300x200")
window.resizable(False, False)

shift_status_var = StringVar()
shift_status_var.set(f"Смена - {CASHBOX.get_shift_status_caption()}")

cashbox_name_var = StringVar()
cashbox_name_var.set(f"{CASHBOX.name}, НОМЕР {CASHBOX.serial_number}")

service_status_var = StringVar()
service_status_var.set(f"Отсутствует cоединение с сервером")

server_status_label = Label(textvariable=service_status_var)

cashbox_label = Label(textvariable=cashbox_name_var)
shift_status_label = Label(textvariable=shift_status_var)

setup_cashbox_button = Button(text="Настроить кассу", command=connect_cashbox)

open_shift_button = Button(text="Открыть смену", command=open_shift)
close_shift_button = Button(text="Закрыть смену", command=close_shift)
x_report_button = Button(text="X-отчет")
z_report_button = Button(text="Z-отчет")
#log_list = Scrollbar(orient="vertical")

for c in window.children:
    window.children[c].pack()


WINDOW_HANDLER = window.winfo_id()
