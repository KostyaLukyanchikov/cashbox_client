## Запуск
!Важно: драйвер АТОЛ 10 должен быть установлен для работы с кассой
```
poetry install
pytnon src/main.py
```

## Настройка
Настройки хранятся в файле config.json, который при первом запуске создается в `~/Users/<user>/AppData/Local/CashboxClient`.

В этом файле можно указать `server_address` - IP адрес сервера, к которому будет осуществляться подключения.make
Так же там есть секции: `theme`, `tabs`, которые отвечают за цветовую тему приложения и настроек вкладок.

## Сборка
Процесс сборки автоматизирован и включает в себя лишь запуск команды `poetry run build-installer`.
Подробнее шаги сборки можно посмотреть в файле `build.py`

Что необходимо для сборки:
1. В папке `./drivers` должны находиться файлы: `KKT10-10.10.0.0-windows32-setup.exe`, `KKT10-10.10.0.0-windows64-setup.exe`
2. В папке `/static` должен находиться файл `icon.ico`. 

