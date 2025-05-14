import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Настройки
API_TOKEN = '7423076499:AAH5I_8iaOleEvoosfdlwVcPhKem03WMnwE'  # Замените на токен от @BotFather
ADMIN_PANEL_URL = 'http://127.0.0.1:8000/admin/login/?next=/admin/'  # Ваш URL админки

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем reply-кнопку
work_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Хочу поработать")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


# Обработчик команды /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.answer(
        "Привет! Это бот Администратора сайта Цветы в Минске",
        reply_markup=work_keyboard
    )


# Обработчик кнопки "Хочу поработать"
@dp.message(F.text ==  "Хочу поработать")
async def work_handler(message: types.Message):
    # Создаем inline-кнопку
    inline_btn = InlineKeyboardButton(
        text="Заходи в Админ панель",
        url=ADMIN_PANEL_URL
    )
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[inline_btn]])

    await message.answer(
        "Нет проблем!",
        reply_markup=inline_kb
    )

# Создаем асинхронную функцию main, которая будет запускать наш бот
async def main():
    await dp.start_polling(bot)

# Запуск бота
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())