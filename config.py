from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import mysql.connector

"""""
Конфигурация базы данных
"""""
DB_CONFIG = {
    'host': 'server160.hosting.reg.ru',
    'port': 3306,
    'user': 'u1585489_tan',
    'password': 'iN4hZ1vN0kzJ4zP3',
    'database': 'u1585489_tanami'
}

API_TOKEN = '' # Токен получить из @BotFather
admins = [2004291407] # Список администраторов, добавлять через запятую
editors = 'editors.json' # Название файла с редакторами

bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor()
