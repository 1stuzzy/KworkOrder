from aiogram.dispatcher.filters.state import StatesGroup, State


class ArticleStates(StatesGroup):
    waiting_for_article_number = State()
    waiting_for_new_editor = State()
    waiting_for_editor_to_remove = State()