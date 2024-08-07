# FAQ

## Содержание
1. [Как установить Python 3.10?](#как-установить-python-310)
2. [Как установить зависимости?](#как-установить-зависимости)
3. [Как настроить бота?](#как-настроить-бота)
4. [Как запустить бота?](#как-запустить-бота)

## Как установить Python 3.10?

Для запуска бота Вам потребуется Python версии 3.10. Вы можете скачать его по [этой ссылке](https://www.python.org/downloads/release/python-31014/). При установке на Windows обязательно отметьте галочку "ADD PYTHON TO PATH".

## Как установить зависимости?

Для установки зависимостей выполните следующие шаги:

1. Откройте Windows-консоль.
2. Перейдите в папку с ботом:
    ```bash
    cd [путь к папке]
    ```
3. Установите зависимости и библиотеки:
    ```bash
    pip install -r requirements.txt
    ```

## Как настроить бота?

Настройте бота в файле `config.py`. Внутри файла все параметры подписаны и объяснены.

## Как запустить бота?

Запустите бота с помощью следующей команды:
```bash
python app.py
