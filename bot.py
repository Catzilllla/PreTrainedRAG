import logging
import telebot
from telebot import types
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util
import chromadb
from chromadb.config import Settings
import os

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "@tgChannelForm")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "deep-seek-tok")
EMBEDDING_MODEL = "mxbai-embed-large"

bot = telebot.TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# --- Загрузка услуг ---
df = pd.read_csv("rag_services.csv")
services = df["Услуга"].tolist()
prices = df["Стоимость (руб.)"].tolist()

# --- Подключение к ChromaDB с эмбеддингами ---
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("auto_services")

# --- Состояние пользователя ---
user_state = {}

# --- Главное меню ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚗 Запись на сервис"), types.KeyboardButton("🔧 Описать проблему"))
    return markup

# --- Start ---
@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Я помогу вам записаться на автосервис или узнать стоимость услуги.", reply_markup=main_menu())

# --- Обработка кнопок ---
@bot.message_handler(func=lambda m: m.text == "🚗 Запись на сервис")
def handle_booking(message):
    user_state[message.chat.id] = {"step": "name"}
    bot.send_message(message.chat.id, "Как вас зовут?")

@bot.message_handler(func=lambda m: m.text == "🔧 Описать проблему")
def handle_problem_start(message):
    bot.send_message(message.chat.id, "Опишите, пожалуйста, проблему с автомобилем.")

# --- Сбор информации ---
@bot.message_handler(func=lambda message: user_state.get(message.chat.id, {}).get("step") is not None)
def handle_data_collection(message):
    user = user_state.setdefault(message.chat.id, {})

    if user["step"] == "name":
        user["name"] = message.text
        user["step"] = "phone"
        bot.send_message(message.chat.id, "Введите ваш номер телефона:")
    elif user["step"] == "phone":
        user["phone"] = message.text
        user["step"] = "car"
        bot.send_message(message.chat.id, "Марка и модель автомобиля:")
    elif user["step"] == "car":
        user["car"] = message.text
        user["step"] = "issue"
        bot.send_message(message.chat.id, "Опишите проблему:")
    elif user["step"] == "issue":
        user["issue"] = message.text
        user["step"] = "time"
        bot.send_message(message.chat.id, "Укажите желаемое время записи:")
    elif user["step"] == "time":
        user["time"] = message.text
        send_request_to_admin(message.chat.id)
        del user_state[message.chat.id]
        bot.send_message(message.chat.id, "Спасибо! Мы свяжемся с вами в ближайшее время.", reply_markup=main_menu())

# --- Отправка заявки администратору ---
def send_request_to_admin(user_id):
    user = user_state[user_id]
    text = (
        f"🆕 Заявка на сервис:\n"
        f"👤 Имя: {user['name']}\n"
        f"📱 Телефон: {user['phone']}\n"
        f"🚘 Автомобиль: {user['car']}\n"
        f"🔧 Проблема: {user['issue']}\n"
        f"🕓 Время: {user['time']}"
    )
    bot.send_message(ADMIN_CHAT_ID, text)
    logging.info(f"Заявка отправлена: {text}")

# --- Поиск услуги по проблеме ---
@bot.message_handler(func=lambda m: True)
def handle_problem_search(message):
    query = message.text
    results = collection.query(query_texts=[query], n_results=1)
    
    if not results["documents"]:
        bot.send_message(message.chat.id, "Услуга не найдена. Вот список доступных:", reply_markup=None)
        service_list = "\n".join(f"{s} — {p} руб." for s, p in zip(services, prices))
        bot.send_message(message.chat.id, service_list)
    else:
        matched_service = results["documents"][0][0]
        idx = services.index(matched_service)
        response = f"✅ Предлагаем услугу: {matched_service}\n💰 Стоимость: {prices[idx]} руб."
        bot.send_message(message.chat.id, response)

# --- Запуск ---
if __name__ == "__main__":
    logging.info("Бот запущен.")
    bot.infinity_polling()
