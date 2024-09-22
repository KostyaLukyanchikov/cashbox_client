import logging
import os
import subprocess

BASE_DIR = ".build"
STATIC_DIR = "static"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def export_requirements():
    """Экспортирует зависимости из poetry.lock в requirements.txt"""
    requirements_path = f"{BASE_DIR}/requirements.txt"
    logging.info("Экспортирование зависимостей в requirements.txt...")

    result = subprocess.run(
        [
            "poetry",
            "export",
            "-f",
            "requirements.txt",
            "--output",
            requirements_path,
            "--without-hashes",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        logging.info(f"requirements.txt успешно создан в {requirements_path}")
    else:
        logging.error("Ошибка при создании requirements.txt:")
        logging.error(result.stdout)
        raise Exception(result.stderr)


def build_pyinstaller():
    build_dir = f"{BASE_DIR}/build"
    dist_dir = f"{BASE_DIR}/dist"
    spec_dir = BASE_DIR

    # Создаем каталоги, если они не существуют
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)

    # Определяем полный путь до иконки
    static_path = os.path.abspath(f"{STATIC_DIR}")
    icon_path = os.path.join(static_path, "icon.ico")

    logging.info("Начало сборки PyInstaller...")
    pyinstaller_cmd = [
        "pyinstaller",
        "--windowed",
        "main.py",
        "-n",
        "Cashbox client",
        "-y",
        "--distpath",
        dist_dir,
        "--workpath",
        build_dir,
        "--specpath",
        spec_dir,
        "--icon",
        icon_path,
        "--add-data",
        f"{static_path};static",
    ]

    result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)

    if result.returncode == 0:
        logging.info("Сборка PyInstaller завершена успешно.")
    else:
        logging.error("Ошибка во время сборки PyInstaller:")
        logging.error(result.stdout)
        raise Exception(result.stderr)


def build_inno_setup():
    inno_setup_path = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    script_path = "installer_script.iss"
    installer_dir = f"{BASE_DIR}/installer"

    if not os.path.exists(inno_setup_path):
        logging.error(f"Inno Setup не найден по пути: {inno_setup_path}")
        return

    if not os.path.exists(script_path):
        logging.error(f"Скрипт Inno Setup не найден по пути: {script_path}")
        return

    os.makedirs(installer_dir, exist_ok=True)

    logging.info("Запуск сборки через Inno Setup...")
    result = subprocess.run(
        [inno_setup_path, script_path], capture_output=True, text=True
    )

    if result.returncode == 0:
        logging.info("Сборка Inno Setup завершена успешно.")
    else:
        logging.error("Ошибка во время сборки Inno Setup:")
        logging.error(result.stdout)
        raise Exception(result.stderr)


def full_build():
    os.makedirs(BASE_DIR, exist_ok=True)

    logging.info("Запуск полного процесса сборки...")

    export_requirements()
    build_pyinstaller()
    build_inno_setup()

    logging.info("Процесс сборки завершен.")
