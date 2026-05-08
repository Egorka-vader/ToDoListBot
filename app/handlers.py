from aiogram.types import Message,CallbackQuery,InlineKeyboardMarkup,InlineKeyboardButton,ReplyKeyboardMarkup,KeyboardButton,PreCheckoutQuery, LabeledPrice
from aiogram.filters import CommandStart,Command
from aiogram.fsm.state import State,StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Router,F,Bot
from ToDoList.database import SessionLocal, User, BroadCast
from ToDoList.config import ADMIN_ID,TOKEN
from datetime import datetime
from ToDoList.app.keyboard import start_keyboard
import time
import datetime
from sqlalchemy.orm import attributes

bot = Bot(token=TOKEN)
router = Router()



payment = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оплатить ⭐', pay=True)]
])

class Task(StatesGroup):
    task_text = State()
    waiting_for_due_date = State()


class BroadcastState(StatesGroup):
    wait_text = State()


def admin_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊‍ Статистика", callback_data='stats')],
        [InlineKeyboardButton(text='✉️ Рассылка', callback_data='broadcast')],
        [InlineKeyboardButton(text='⚙️ Доп настройки', callback_data='settings')]
    ])
    return keyboard


def back_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Back', callback_data='back')],
    ])
    return keyboard


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Добро пожаловать в админ панель бота 🌍❤️❤️!", reply_markup=admin_main_menu())
        return
    else:
        await message.answer('У вас нет доступа к этой команде.')
        return



@router.callback_query(F.data == 'back')
async def back_menu(callback: CallbackQuery):
    await callback.message.answer("", reply_markup=admin_main_menu())
    await callback.answer('')


@router.callback_query(F.data == 'stats')
async def stats_process(callback: CallbackQuery):
    db = SessionLocal()
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.active == True).count()
    db.close()
    text = f'Статистика:\nВсего пользователей 🕵️: {total_users}\nАктивных пользователей 🎮: {active_users}'
    await callback.message.answer(f'{text}')
    await callback.answer('')


@router.callback_query(F.data == 'broadcast')
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст для рассылки ✉️")
    await state.set_state(BroadcastState.wait_text)
    await callback.answer('')


@router.callback_query(F.data == 'settings')
async def settings(callback: CallbackQuery):
    await callback.message.answer("Я рома тик так ")
    await callback.answer('')


@router.message(BroadcastState.wait_text)
async def broadcast_mess(message: Message, state: FSMContext, bot: Bot):
    broadcast_text = message.text
    db = SessionLocal()
    users_list = db.query(User).filter(User.active == True).all()
    count = 0
    for user in users_list:
        try:
            await bot.send_message(str(user.telegram_id), broadcast_text)
            count += 1
        except Exception as e:
            print(f'Failed to send to {user.telegram_id}:{e}')
    new_broadcast = BroadCast(message=broadcast_text)
    db.add(new_broadcast)
    db.commit()
    db.close()
    await message.answer(f"Рассылка завершена ✉️ ! Сообщение отправлено {count} пользователям 🕵️."
                        )
    await state.clear()


@router.message(CommandStart())
async def start(message: Message):

    db = SessionLocal()

    exiting = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
    if not exiting:

        new_user = User(telegram_id=str(message.from_user.id), name=message.from_user.full_name,
                        register_at=datetime.now().isoformat())
        db.add(new_user)
        db.commit()
    db.close()

    if message.from_user.id == ADMIN_ID:
        db = SessionLocal()

        user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
        if user:
            user.premium = True

            db.commit()
        db.close()

    await message.answer_photo(
        photo='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLOf4S-daqBsqdG-k3iTg7jlH04ptJiSwQXg&s',
        caption=f"<b>Приветствую!</b> 🌿 Рад видеть тебя здесь.\nЭтот бот поможет тебе:\n\nСтруктурировать мысли\nДоводить дела до конца\nНаходить время для важного\n\nНачни с малого — добавь одну задачу на сегодня.\nИ помни: маленькие шаги ведут к большим целям. 🚶‍♂️✨\n\nТвои действия — в <b>меню</b> ниже 👇",
        parse_mode='HTML',reply_markup=start_keyboard)

@router.callback_query(F.data == 'premium')
async def premium_get(callback:CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔑 Подписка ', callback_data='subscribe')],
        [InlineKeyboardButton(text='🤝 Поддержка бота', callback_data='support_bot')]
    ])
    await callback.answer('')
    await callback.message.answer('🔃 Выберите вариант:', reply_markup=keyboard)

@router.callback_query(F.data == 'subscribe')
async def premium_getting(callback: CallbackQuery):
    prices = [LabeledPrice(label="XTR", amount=250)]

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(callback.from_user.id)).first()

    if user and user.premium:
        await callback.answer('❌ У вас уже есть подписка!', show_alert=True)
        db.close()
        return

    db.close()
    await callback.answer('')

    await callback.message.answer_invoice(
        title='🔑 Premium подписка',
        description='• Доступ к расширенному поиску\n• Приоритетная поддержка',
        prices=prices,
        provider_token='',
        payload='premium_subscription',
        currency='XTR',
        reply_markup=payment
    )


@router.callback_query(F.data == 'support_bot')
async def support_to_bot(callback: CallbackQuery):
    prices = [LabeledPrice(label="XTR", amount=20)]
    await callback.answer('')

    await callback.message.answer_invoice(
        title='🤝 Поддержка бота',
        description='Поддержите разработку бота звездами ⭐',
        prices=prices,
        provider_token='',
        payload='bot_support',
        currency='XTR',
        reply_markup=payment,
    )


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payment_system = message.successful_payment
    payload = payment.invoice_payload  # Получаем payload
    user_id = str(message.from_user.id)

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()

    if not user:

        user = User(telegram_id=user_id, name=message.from_user.full_name)
        db.add(user)
        db.commit()

    # Обрабатываем разные типы платежей
    if payload == 'premium_subscription':
        # Покупка подписки
        user.premium = True

        db.commit()

        await message.answer(
            f"✅ **Premium 🔑Подписка активирована!**\n\n"
            f"⭐ Получено: {payment.total_amount} звёзд\n"
            f"Спасибо за покупку! 🎉",
             message_effect_id="5104841245755180586"


        )

    elif payload == 'bot_support':

        await message.answer(
            f"🎉 **Спасибо за поддержку!** 🎉\n\n"
            f"⭐ Получено: {payment.total_amount} звёзд\n"
            f"👤 От: {message.from_user.full_name}\n\n"
            f"💝 Ваша поддержка помогает боту развиваться!",
            message_effect_id="5104841245755180586"
        )

    db.close()


@router.callback_query(F.data == 'profile')
async def profile_answer(callback:CallbackQuery):
    db = SessionLocal()

    user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()

    register_at = user.register_at
    premium = user.premium
    if premium is True:
        premium = '✅'
    else:
        premium = '❌'

    await callback.answer('')

    db.close()
    await callback.message.reply(
        f'ℹ️ Вся необходимая информация о вашем профиле\n\n🏷️ <b>Имя:</b> <a href="tg://copy?text=ddddd">{callback.from_user.full_name}</a>\n🔗<b>Username:</b> @{callback.from_user.username}\n\n🆔 <b>Мой ID:</b> <a href="tg://copy?text=ddddddd">{callback.message.from_user.id}</a>\n📆 <b>Регистрация:</b> <a href="tg://copy?text=fdddd">{register_at}</a>\n🔃 <b>TG Премиум:</b> {callback.message.from_user.is_premium}\n\n🔑 <b>Подписка:</b> {premium}\n🗣️ <b>Язык:</b> <b>{callback.message.from_user.language_code}</b>\n\n💰 Твой баланс: <a href="tg://copy?text=0.00">0.00 RUB</a>\n',
         parse_mode="HTML",reply_markup=start_keyboard)


@router.callback_query(F.data == 'add_task')
async def added_task_step(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.answer('📋 Введи текст задачи, которую ты хочешь выполнить:')
    await state.set_state(Task.task_text)


@router.message(Task.task_text)
async def date_check(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text.strip())
    await message.answer('📆 Введите дату, до которой нужно выполнить задачу (например: 2024-12-31):')
    await state.set_state(Task.waiting_for_due_date)


@router.message(Task.waiting_for_due_date)
async def add_task(message: Message, state: FSMContext):
    data = await state.get_data()
    task_text = data.get('task_text')
    due_date = message.text.strip()

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()

    if user:
        tasks = list(user.tasks) if user.tasks else []

        new_task = {
            "id": int(time.time() * 1000),
            "text": task_text,
            "due_date": due_date,
            "completed": False,
            "created_at": datetime.datetime.now().isoformat()
        }
        tasks.append(new_task)

        user.tasks = tasks
        attributes.flag_modified(user, 'tasks')
        db.commit()

        await message.answer(f'✅ Задача "{task_text}" успешно добавлена!\n📅 Дедлайн: {due_date}')
    else:
        await message.answer('❌ Пользователь не найден. Напишите /start')

    db.close()
    await state.clear()


@router.callback_query(F.data == 'task_list')
async def task_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(user_id)).first()

    if not user or not user.tasks:
        await callback.answer("📭 У вас пока нет задач!", show_alert=True)
        db.close()
        return

    # Показываем ВСЕ задачи (сначала активные, потом выполненные)
    active_tasks = [task for task in user.tasks if not task.get('completed', False)]
    completed_tasks = [task for task in user.tasks if task.get('completed', False)]
    all_tasks = active_tasks + completed_tasks

    db.close()

    if not all_tasks:
        await callback.answer("📭 У вас пока нет задач!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for task in all_tasks:
        task_text = task.get('text', 'Без названия')[:30]
        is_completed = task.get('completed', False)
        emoji = "✅" if is_completed else "📌"

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {task_text}",
                callback_data=f"view_task_{task.get('id')}"
            )
        ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")
    ])

    try:
        await callback.message.edit_text(
            "📋 **Список задач:**\n\n"
            "📌 — активные\n"
            "✅ — выполненные\n\n"
            "Нажмите на задачу для просмотра подробностей",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception:
        await callback.message.answer(
            "📋 **Список задач:**\n\n"
            "📌 — активные\n"
            "✅ — выполненные\n\n"
            "Нажмите на задачу для просмотра подробностей",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    await callback.answer()


@router.callback_query(F.data.startswith('view_task_'))
async def view_task(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(user_id)).first()

    if not user or not user.tasks:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        db.close()
        return

    # Ищем задачу
    found_task = None
    for task in user.tasks:
        if task.get('id') == task_id:
            found_task = task
            break

    db.close()

    if not found_task:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return

    # Форматируем статус
    is_completed = found_task.get('completed', False)
    status = "✅ Выполнена" if is_completed else "⏳ В процессе"
    status_emoji = "✅" if is_completed else "⏳"

    # Форматируем дату
    due_date = found_task.get('due_date', 'Не указана')
    created_at = found_task.get('created_at', 'Неизвестно')
    if len(created_at) > 10:
        created_at = created_at[:10]

    # Клавиатура с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выполнить", callback_data=f"complete_task_{task_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_task_{task_id}")
        ],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="task_list")]
    ])

    # Формируем сообщение
    task_info = (
        f"📋 <b>Информация о задаче</b>\n\n"
        f"📝 <b>Текст:</b> <code>{found_task.get('text')}</code>\n"
        f"📅 <b>Дедлайн:</b> <code>{due_date}</code>\n"
        f"🔘 <b>Статус:</b> {status_emoji} {status}\n"
        f"🆔 <b>ID задачи:</b> <code>{task_id}</code>\n"
        f"📆 <b>Создано:</b> <code>{created_at}</code>\n"
    )

    if is_completed:
        task_info += f"✅ <b>Выполнена!</b>\n"

    await callback.message.edit_text(
        task_info,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith('complete_task_'))
async def complete_task(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(user_id)).first()

    if user and user.tasks:
        task_found = False
        for task in user.tasks:
            if task.get('id') == task_id:
                task['completed'] = True
                task_found = True
                break

        if task_found:
            attributes.flag_modified(user, 'tasks')
            db.commit()
            await callback.answer("✅ Задача отмечена как выполненная!")

            # Показываем обновлённую карточку задачи
            await view_task(callback)
        else:
            await callback.answer("❌ Задача не найдена", show_alert=True)
    else:
        await callback.answer("❌ Задача не найдена", show_alert=True)

    db.close()


@router.callback_query(F.data.startswith('delete_task_'))
async def delete_task(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id

    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == str(user_id)).first()

    if user and user.tasks:
        old_count = len(user.tasks)

        # Удаляем задачу
        user.tasks = [task for task in user.tasks if task.get('id') != task_id]

        if len(user.tasks) < old_count:
            attributes.flag_modified(user, 'tasks')
            db.commit()
            await callback.answer("🗑️ Задача удалена!")

            # Возвращаемся к списку задач
            await task_list(callback)
        else:
            await callback.answer("❌ Задача не найдена", show_alert=True)
    else:
        await callback.answer("❌ Задача не найдена", show_alert=True)

    db.close()

