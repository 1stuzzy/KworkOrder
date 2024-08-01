import json
from config import admins


def load_editors():
    """
    Загрузить данные редакторов из файла editors.json.

    Returns:
        dict: Словарь с данными редакторов.
    """
    try:
        with open('editors.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON в файле editors.json")
        return {}


def save_editors(editors):
    """
    Сохранить данные редакторов в файл editors.json.

    Args:
        editors (dict): Словарь с данными редакторов.
    """
    try:
        with open('editors.json', 'w', encoding='utf-8') as file:
            json.dump(editors, file, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Ошибка записи файла editors.json: {e}")


def is_editor(user_id):
    """
    Проверить, является ли пользователь редактором или администратором.

    Args:
        user_id (int): ID пользователя для проверки.

    Returns:
        bool: True, если пользователь является редактором или администратором, иначе False.
    """
    if is_admin(user_id):
        return True

    editors = load_editors()
    return str(user_id) in editors


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in admins