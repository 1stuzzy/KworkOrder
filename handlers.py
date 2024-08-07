import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified
from loguru import logger
from config import dp, bot, admins
from functions import is_editor, is_admin, load_editors
from states import ArticleStates
from database import (get_articles, get_article_by_id, update_article_status,
                      get_user_article_status_history, count_user_articles, get_url)

user_data = {}


@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message):
    user_id = message.from_user.id

    if not (is_editor(user_id) or is_admin(user_id)):
        logger.error(f'Access denied [{user_id}]')

        await message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton("📕 Список статей", callback_data="get_articles"),
        types.InlineKeyboardButton("🔎 Поиск статьи", callback_data="search_article"),
        types.InlineKeyboardButton("📃 История статей", callback_data="status_history"),
    ]

    if is_admin(user_id):
        logger.info(f'Admin [{user_id}] - True')
        admin_buttons = [
            types.InlineKeyboardButton("➕ Панель администратора", callback_data="more_options")
        ]
        buttons.extend(admin_buttons)

    markup.add(*buttons)
    await message.reply("<b>📋 Главное меню</b>", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data == 'more_options')
async def handle_more_options(callback_query: types.CallbackQuery):

    user_id = callback_query.from_user.id
    if is_admin(user_id):
        logger.info(f'Admin [{user_id}] - True')
        markup = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton("➕ Добавить редактора", callback_data="add_editor"),
            types.InlineKeyboardButton("➖ Удалить редактора", callback_data="remove_editor"),
            types.InlineKeyboardButton("👥 Список редакторов", callback_data="list_editors")
        ]

        markup.add(*buttons)

        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        except Exception as e:
            logger.exception(f'{e}')
            pass

        await callback_query.message.answer("📃 <b>Выберите опцию:</b>", reply_markup=markup)
        await callback_query.answer()


@dp.callback_query_handler(lambda call: call.data == "get_articles", state='*')
async def get_articles_callback(call: types.CallbackQuery):
    user_id = call.from_user.id

    if not (is_editor(user_id) or is_admin(user_id)):
        logger.error(f'Access denied [{user_id}]')
        await call.message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    await show_and_display_articles(call.message, user_id)


async def show_and_display_articles(message: types.Message, user_id: int):
    user_data[user_id] = {
        'articles': [],
        'page': 1,
        'num_pages': 0,
        'sort_order': 'asc',
        'status_filter': None,
        'message_id': None
    }
    await display_articles(message, user_id)


async def display_articles(message: types.Message, user_id: int):
    data = user_data.get(user_id, {})
    page = data.get('page', 1)
    sort_order = data.get('sort_order', 'asc')
    status_filter = data.get('status_filter', None)

    articles = get_articles(status_filter, sort_order)
    num_pages = (len(articles) + 10 - 1) // 10
    user_data[user_id].update({'articles': articles, 'num_pages': num_pages})

    start = (page - 1) * 10
    end = start + 10
    articles_to_show = articles[start:end]

    response = f"📋 <b>Список статей:</b>\n\n" + \
               "\n".join(f"<b><i>/article{article_id} - {status}</i></b>" for article_id, status in articles_to_show)

    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = []

    if page > 1:
        buttons.append(types.InlineKeyboardButton("◀️", callback_data="prev"))
    else:
        buttons.append(types.InlineKeyboardButton("◀️", callback_data="no_op"))

    buttons.append(types.InlineKeyboardButton(f"{page}/{num_pages}", callback_data="no_op"))

    if page < num_pages:
        buttons.append(types.InlineKeyboardButton("▶️", callback_data="next"))
    else:
        buttons.append(types.InlineKeyboardButton("▶️", callback_data="no_op"))

    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("📑 Сортировка", callback_data="sort"))
    markup.add(types.InlineKeyboardButton("🔎 Найти статью", callback_data="search_article"))

    if data.get('message_id'):
        try:
            await bot.edit_message_text(response, message.chat.id, message_id=data['message_id'])
            await bot.edit_message_reply_markup(message.chat.id, message_id=data['message_id'], reply_markup=markup)
        except MessageNotModified:
            pass
    else:
        sent_message = await message.answer(response, reply_markup=markup)
        user_data[user_id]['message_id'] = sent_message.message_id


@dp.callback_query_handler(lambda call: call.data in ["prev", "next"], state='*')
async def handle_navigation(call: types.CallbackQuery):
    user_id = call.from_user.id
    data = user_data.get(user_id, {})
    page = data.get('page', 1)

    if call.data == "prev":
        if page > 1:
            user_data[user_id]['page'] -= 1
    elif call.data == "next":
        if page < user_data[user_id].get('num_pages', 1):
            user_data[user_id]['page'] += 1

    await display_articles(call.message, user_id)


@dp.callback_query_handler(lambda c: c.data == 'sort')
async def handle_sorting_options(callback_query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("По возрастанию 🔼", callback_data="sort_asc"),
        types.InlineKeyboardButton("По убыванию 🔽", callback_data="sort_desc"),
    )
    await callback_query.message.answer("📑 <b>Выберите способ сортировки:</b>", reply_markup=markup)
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('sort_'))
async def handle_sorting(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    sort_type = callback_query.data.split('_')[1]

    if sort_type == 'asc':
        user_data[user_id]['sort_order'] = 'asc'
    elif sort_type == 'desc':
        user_data[user_id]['sort_order'] = 'desc'

    user_data[user_id]['page'] = 1
    await display_articles(callback_query.message, user_id)
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'search_article')
async def handle_search_article(callback_query: types.CallbackQuery, state: FSMContext):
    await ArticleStates.waiting_for_article_number.set()

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))

    await callback_query.message.answer("✍️ <b>Введите номер статьи:</b>", reply_markup=markup)
    await callback_query.answer()


@dp.message_handler(state=ArticleStates.waiting_for_article_number)
async def handle_article_number(message: types.Message, state: FSMContext):
    try:
        article_id = int(message.text.strip())
        article = get_article_by_id(article_id)

        if article:
            response = f"✅ <b>Статья найдена:</b>\n\n<b><i>/article{article[0]} - {article[1]}</i></b>"
        else:
            response = "❌ <i>Статья с таким номером не найдена.</i>"

        await message.answer(response)
    except ValueError:
        await message.answer("❌ <i>Пожалуйста, введите корректный номер статьи.</i>")

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'back_to_menu', state=ArticleStates.waiting_for_article_number)
async def handle_back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if not (is_editor(user_id) or is_admin(user_id)):
        logger.error(f'Access denied [{user_id}]')

        await callback_query.message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    await state.finish()

    try:
        await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)
    except Exception as e:
        logger.exception(f'{e}')
        pass

    await show_and_display_articles(callback_query.message, user_id)

    await callback_query.answer()


@dp.message_handler(lambda message: message.text.startswith('/article'))
async def article_details(message: types.Message):
    user_id = message.from_user.id
    if not (is_editor(user_id) or is_admin(user_id)):
        logger.error(f'Access denied [{user_id}]')
        await message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    text = message.text.strip()
    if not text.startswith('/article'):
        await message.answer("❌ Неверный формат команды. Используйте <i>/article{номер статьи}</i>.")
        return

    article_id_str = text[len('/article'):].strip()
    if not article_id_str.isdigit():
        await message.answer("❌ <i>Неверный формат команды. Введите номер статьи после команды /article.</i>")
        return

    article_id = int(article_id_str)
    article = get_article_by_id(article_id)
    links = get_url(article_id)

    if article and links:
        status = article[1]
        external_link, internal_link = links
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("Начал ✅", callback_data=f"start_{article_id}"),
            types.InlineKeyboardButton("Закончил 🔒", callback_data=f"done_{article_id}"),
            types.InlineKeyboardButton("На проверке 🛠", callback_data=f"review_{article_id}")
        ]
        markup.add(*buttons)
        await message.answer(
            f"📄 <b>Статья:</b> <code>{article_id}</code>\n"
            f"ℹ️ <b>Статус:</b> <code>{status}</code>\n\n"
            f"🔗 <b>Внешняя ссылка:</b> <a href='{external_link}'>{external_link}</a>\n"
            f"🔗 <b>Внутренняя ссылка:</b> <i><a href='{internal_link}'>Редактировать</a></i>",
            reply_markup=markup, disable_web_page_preview=True
        )
    else:
        await message.answer("<i>❌ Статья с таким номером не найдена.</i>")
       




@dp.callback_query_handler(lambda c: c.data.startswith(('start_', 'done_', 'review_')))
async def change_status(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if not (is_editor(user_id) or is_admin(user_id)):
        logger.error(f'Access denied [{user_id}]')

        await callback_query.message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    action, article_id = callback_query.data.split('_')
    article_id = int(article_id)
    status = action.upper()

    update_article_status(article_id, user_id, status)

    new_message_text = f"<b>Статус статьи <code>{article_id}</code> изменён на <code>{status}</code>.</b>"

    await callback_query.answer(f"📝 Статус статьи {article_id} изменён на {status}.")

    try:
        await callback_query.message.edit_text(new_message_text)
        await callback_query.message.edit_reply_markup(callback_query.message.reply_markup)
    except Exception as e:
        await callback_query.message.answer(new_message_text)

    await callback_query.message.answer(f"📝 <b>Статус статьи {article_id} изменён на <code>{status}</code>.</b>")
    for admin in admins:
        await bot.send_message(admin, f"📝 <b>Статус статьи {article_id} изменён на <code>{status}</code></b>\n\n"
                                      f"<b>👤 Редактировал:</b>\n"
                                      f"<b>└ ID: <code>{user_id}</code>\n"
                                      f"└ Username: @{callback_query.from_user.username}\n"
                                      f"└ Name: {callback_query.from_user.full_name}</b>")


@dp.callback_query_handler(lambda c: c.data == 'status_history')
async def handle_status_history(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if not (is_editor(user_id) or is_admin(user_id)):
        await callback_query.message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    limit = 5
    offset = 0

    history = get_user_article_status_history(user_id, limit, offset)
    total_count = count_user_articles(user_id)

    response = "📃 <b>История статей:</b>\n\n"

    if history:
        response += "\n".join([f"<b>Статья:</b> <code>{item[0]}</code> - <b>Статус:</b> <code>{item[1]}</code>" for item in history])
        markup = types.InlineKeyboardMarkup(row_width=2)
        if offset + limit < total_count:
            next_button = types.InlineKeyboardButton("➡️ Следующая страница", callback_data=f"history_page_{offset + limit}")
            markup.add(next_button)
    else:
        response = "У вас нет изменений в статьях."
        markup = None

    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    except Exception as e:
        pass

    await callback_query.message.answer(response, reply_markup=markup, parse_mode='HTML')
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('history_page_'))
async def handle_history_pagination(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    offset = int(callback_query.data.split('_')[-1])
    limit = 5

    history = get_user_article_status_history(user_id, limit, offset)
    total_count = count_user_articles(user_id)

    response = "📃 <b>История статей:</b>\n\n"

    if history:
        response += "\n".join([f"<b>Статья:</b> <code>{item[0]}</code> - <b>Статус:</b> <code>{item[1]}</code>" for item in history])
        markup = types.InlineKeyboardMarkup(row_width=2)
        if offset > 0:
            prev_button = types.InlineKeyboardButton("⬅️", callback_data=f"history_page_{offset - limit}")
            markup.add(prev_button)
        if offset + limit < total_count:
            next_button = types.InlineKeyboardButton("➡️", callback_data=f"history_page_{offset + limit}")
            markup.add(next_button)
    else:
        response = "У вас нет изменений в статьях."
        markup = None

    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    except Exception as e:
        pass

    await callback_query.message.answer(response, reply_markup=markup, parse_mode='HTML')
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == 'add_editor')
async def handle_add_editor(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if is_admin(user_id):
        await ArticleStates.waiting_for_new_editor.set()

        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        except Exception as e:
            pass

        await callback_query.message.answer("✍️ <b>Введите ID пользователя для добавления в редакторы:</b>")
        await callback_query.answer()


@dp.message_handler(state=ArticleStates.waiting_for_new_editor)
async def add_editor(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    try:
        new_editor_id = int(message.text.strip())
    except ValueError:
        await message.answer("⛔️ <b>Введите корректный ID пользователя.</b>")
        return

    editors = load_editors()

    if str(new_editor_id) in editors:
        await message.answer("⛔️ <b>Этот пользователь уже является редактором.</b>")
    else:
        editors[str(new_editor_id)] = {
            "username": "Не указан",
            "name": "Не указано"
        }
        with open('editors.json', 'w', encoding='utf-8') as file:
            json.dump(editors, file, ensure_ascii=False, indent=4)
        await message.answer(f"✅ <b>Пользователь с ID {new_editor_id} добавлен в редакторы.</b>")

        logger.debug(f'Admin[{user_id}] added editor[{new_editor_id}]')

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'remove_editor')
async def handle_remove_editor(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if is_admin(user_id):
        await ArticleStates.waiting_for_editor_to_remove.set()

        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

        await callback_query.message.answer("✍️ <b>Введите ID пользователя для удаления из редакторов:</b>")
        await callback_query.answer()


@dp.message_handler(state=ArticleStates.waiting_for_editor_to_remove)
async def remove_editor(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if not is_admin(user_id):
        logger.error(f'Access Denied [{user_id}]')
        await message.answer('⛔️ <b><i>У вас нет доступа к данному боту! Обратитесь к заказчику!</i></b>')
        return

    try:
        editor_id_to_remove = int(message.text.strip())
    except ValueError:
        await message.answer("⛔️ <b>Введите корректный ID пользователя.</b>")
        return

    editors = load_editors()

    if str(editor_id_to_remove) not in editors:
        await message.answer("⛔️ <b>Пользователь с таким ID не найден среди редакторов.</b>")
    else:
        del editors[str(editor_id_to_remove)]
        with open('editors.json', 'w', encoding='utf-8') as file:
            json.dump(editors, file, ensure_ascii=False, indent=4)
        await message.answer(f"✅ <b>Пользователь с ID {editor_id_to_remove} удален из редакторов.</b>")
        logger.debug(f'Admin[{user_id}] deleted editor[{editor_id_to_remove}]')

    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'list_editors')
async def handle_list_editors(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if is_admin(user_id):
        editors = load_editors()

        response = "👥 <b>Список редакторов:</b>\n\n"

        if isinstance(editors, dict):
            for editor_id, editor_data in editors.items():
                name = editor_data.get('name', 'Не указано')
                username = editor_data.get('username', 'Не указано')
                response += f"🆔: <code>{editor_id}</code>, Имя: <code>{name}</code>, @{username}\n"
        else:
            response = "Ошибка: Неверный формат данных редакторов."

        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

        await callback_query.message.answer(response, parse_mode=types.ParseMode.HTML)
        await callback_query.answer()