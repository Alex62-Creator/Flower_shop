import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, Message)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import smtplib
from email.message import EmailMessage
from jinja2 import Template
import sqlite3
from catalog.config import TOKEN, EMAIL_HOST_PASSWORD, EMAIL_HOST_USER, ADMIN_PANEL_URL


# Загружаем шаблон письма
template_path = "catalog/templates/emails/status_modify.html"
with open(template_path, "r", encoding="utf-8") as file:
    template_content = file.read()
HTML_TEMPLATE = Template(template_content)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаем reply-кнопки
button_app = KeyboardButton(text="Изменение статуса в приложении")
button_bot = KeyboardButton(text="Изменение статуса в боте")

# Создаем клавиатуру
keyboard = ReplyKeyboardMarkup(keyboard=[
        [button_app, button_bot]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Подключаем БД
conn = sqlite3.connect('db.sqlite3')
conn.row_factory = sqlite3.Row  # Теперь записи будут вести себя как словари
cursor = conn.cursor()


# Создаем класс OrderId для сохранения состояний
class OrderId(StatesGroup):
    order_id = State()
    order_status = State()

# Функция отправки письма пользователю об изменении сиаиуса
def send_status_email(data):
    # Получаем заказ из БД
    cursor.execute('''
               SELECT o.*, u.first_name as user_first_name, u.email as user_email
               FROM catalog_order o
               JOIN catalog_customuser u ON o.user_id = u.id
               WHERE o.id = ?''',
                   (int(data['order_id']),))
    order = cursor.fetchone()

    """Отправка HTML-письма"""
    # Рендерим шаблон
    html_content = HTML_TEMPLATE.render(
        order=order,
        status_display=data['order_status']
    )
    # Формируем письмо
    msg = EmailMessage()
    msg['Subject'] = f'Обновление статуса заказа №{order["id"]}'
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = order['user_email']
    msg.add_alternative(html_content, subtype='html')
    # Отправляем письмо
    try:
        with smtplib.SMTP_SSL('smtp.mail.ru', 465) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

# Обработчик команды /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.answer(        "Привет! Это бот Администратора сайта Цветы в Минске", reply_markup=keyboard)


# Обработчик кнопки "Изменение статуса в приложении"
@dp.message(F.text ==  "Изменение статуса в приложении")
async def app_handler(message: types.Message):
    # Создаем inline-кнопку
    inline_btn = InlineKeyboardButton(text="Заходи в Админ панель", url=ADMIN_PANEL_URL)
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[inline_btn]])
    await message.answer("Войти", reply_markup=inline_kb)

# Обработчик кнопки "Изменение статуса в боте"
@dp.message(F.text ==  "Изменение статуса в боте")
async def bot_handler(message: Message, state: FSMContext):
    await state.set_state(OrderId.order_id)
    await message.reply("Введите номер заказа:")

# Ввод номера заказ
@dp.message(OrderId.order_id)
async def input_id(message: Message, state: FSMContext):
    await state.update_data(order_id = message.text)
    await state.set_state(OrderId.order_status)
    await message.reply("Введите новый статус (pending, paid, delivered, canceled):")

# Ввод нового статуса и сохранение данных в БД
@dp.message(OrderId.order_status)
async def input_id(message: Message, state: FSMContext):
    await state.update_data(order_status = message.text)
    data = await state.get_data()
    # Проверка на корректность статуса
    if data['order_status'] in ('pending', 'paid', 'delivered', 'canceled'):
        cursor.execute(
            '''UPDATE 'catalog_order' SET status = ? WHERE id = ?''',
            (data['order_status'], int(data['order_id'])))
        conn.commit()
        # Отправляем письмо пользователю об обновлении статуса
        success = send_status_email(data)
        await message.answer(f"✅ Статус заказа {data['order_id']} обновлен" if success
                             else "❌ Ошибка отправки уведомления")
    else:
        await message.answer("Некорректный статус. Повторите процедуру изменения статуса.")
    # Очищаем состояния
    await state.clear()


# Создаем асинхронную функцию main, которая будет запускать наш бот
async def main():
    await dp.start_polling(bot)

# Запуск бота
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())