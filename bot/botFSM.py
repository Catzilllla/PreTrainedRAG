import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from chroma_utils import search_service
import httpx


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("ADMIN_CHAT_ID")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

DEEPSEEK_SYSTEM_PROMPT = """
Ты — эксперт автосервиса. Отвечай ясно и профессионально, с учётом задач клиентов по ремонту, диагностике и обслуживанию авто.
"""
OLLAMA_SYSTEM_PROMPT = """
Ты — эксперт автосервиса. Отвечай ясно и профессионально, с учётом задач клиентов по ремонту, диагностике и обслуживанию авто.
"""

# FSM
class SignupForm(StatesGroup):
    name = State()
    phone = State()
    car = State()
    issue = State()
    number = State()
    time = State()

# Главное меню
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🔍 Поиск по услугам")],
    [KeyboardButton(text="📝 Запись на сервис")],
    [KeyboardButton(text="🤖 Agent")],
    [KeyboardButton(text="🤖 llama Agent")],
], resize_keyboard=True)

# /start
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.update_data(mode="agent")
    await message.answer("👋 Привет! Я автосервис-бот. Выберите действие:", reply_markup=main_menu)

# Режимы
@dp.message(F.text == "🔍 Поиск по услугам")
async def mode_chroma(message: Message, state: FSMContext):
    await state.update_data(mode="chromadb")
    await message.answer("✍️ Введите запрос для поиска по базе услуг:")

@dp.message(F.text == "🤖 Agent")
async def mode_deepseek(message: Message, state: FSMContext):
    await state.update_data(mode="agent")
    await message.answer("🤖 Режим DeepSeek активирован. Можешь задавать вопросы.")

@dp.message(F.text == "🤖 llama Agent")
async def mode_ollama(message: Message, state: FSMContext):
    await state.update_data(mode="localagent")
    await message.answer("🤖 Режим локальной модели (Ollama) активирован. Задавай вопрос.")

@dp.message(F.text == "📝 Запись на сервис")
async def signup_start(message: Message, state: FSMContext):
    await state.update_data(mode="signup")
    await message.answer("📋 Введите ваше <b>имя</b> для записи:")
    await state.set_state(SignupForm.name)

# FSM-поток (без изменений)
@dp.message(SignupForm.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Телефон:")
    await state.set_state(SignupForm.phone)

@dp.message(SignupForm.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("🚗 Марка машины:")
    await state.set_state(SignupForm.car)

@dp.message(SignupForm.car)
async def get_car(message: Message, state: FSMContext):
    await state.update_data(car=message.text)
    await message.answer("⚠️ Опишите проблему:")
    await state.set_state(SignupForm.issue)

@dp.message(SignupForm.issue)
async def get_issue(message: Message, state: FSMContext):
    await state.update_data(issue=message.text)
    await message.answer("📞🚗Введи номер машины")
    await state.set_state(SignupForm.number)

@dp.message(SignupForm.number)
async def get_number(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    await message.answer("🕒 Желаемое время:")
    await state.set_state(SignupForm.time)

@dp.message(SignupForm.time)
async def finish_signup(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    data = await state.get_data()
    request_text = (
        "📥 <b>Новая заявка:</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🚗 Машина: {data['car']}\n"
        f"⚠️ Проблема: {data['issue']}\n"
        f"📞🚗 Номер машины: {data['number']}\n"
        f"🕒 Время: {data['time']}"
    )
    await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=request_text)
    await message.answer("✅ Заявка отправлена. Мы скоро свяжемся с вами!", reply_markup=main_menu)
    await state.clear()
    await state.update_data(mode="agent")

# --- Запрос к DeepSeek
async def ask_deepseek(user_input: str) -> str:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# --- Запрос к Ollama
async def ask_ollama(user_input: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": "deepseek-r1:latest",
        "messages": [
            {"role": "system", "content": OLLAMA_SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"]

# Универсальный обработчик
@dp.message(F.text & ~F.text.startswith("/"))
async def handle_input(message: Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("mode", "agent")

    if mode == "chromadb":
        await message.answer("🔎 Поиск по услугам...")
        result = search_service(message.text)
        await message.answer(result)
    elif mode == "agent":
        await message.answer("🤖 Думаю...")
        try:
            reply = await ask_deepseek(message.text)
            await message.answer(reply)
        except Exception as e:
            await message.answer(f"⚠️ Ошибка DeepSeek: {e}")
    elif mode == "localagent":
        await message.answer("🤖 Думаю (локально)...")
        try:
            reply = await ask_ollama(message.text)
            await message.answer(reply)
        except Exception as e:
            await message.answer(f"⚠️ Ошибка Ollama: {e}")
    else:
        await message.answer("❗ Неизвестный режим. Используйте меню.", reply_markup=main_menu)

# Запуск
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))