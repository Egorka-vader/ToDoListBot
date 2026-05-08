from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup,ReplyKeyboardMarkup,KeyboardButton

start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📋Лист задач',callback_data='task_list'),InlineKeyboardButton(text='👤Профиль',callback_data='profile')],
    [InlineKeyboardButton(text='➕ Добавить задачу',callback_data='add_task'),InlineKeyboardButton(text='🔑 Подписка',callback_data='premium')]
])