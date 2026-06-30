import time
import requests
import re
from threading import Thread
import telebot
from telebot import types

TOKEN = '8137721355:AAHBg0luznCyunz699mFgyUyJoSxPCzW6Cc'
URL = 'https://tgftp.nws.noaa.gov/data/observations/metar/stations/UUWW.TXT'

bot = telebot.TeleBot(TOKEN)

# Глобальные переменные для управления
is_running = False
last_temp = None
user_id = None  # Бот будет слать уведомления тому, кто его запустил

def parse_temperature(text):
    """
    Точный парсинг METAR строки.
    Ищет блок вида 22/15 или M02/M05, отделенный пробелами.
    """
    words = text.split()
    for word in words:
        match = re.match(r'^(M?\d{2})/(M?\d{2})$', word)
        if match:
            temp_str = match.group(1)
            if temp_str.startswith('M'):
                return -int(temp_str[1:])
            return int(temp_str)
    return None

    return None

def monitoring_loop():
    global is_running, last_temp, user_id
    
    while True:
        if is_running and user_id:
            try:
                response = requests.get(URL, timeout=5)
                if response.status_code == 200:
                    current_temp = parse_temperature(response.text)
                    
                    if current_temp is not None:
                        if last_temp is None:
                            # Первый запуск, просто сохраняем значение
                            last_temp = current_temp
                            bot.send_message(user_id, f"Мониторинг запущен. Текущая температура во Внуково: {last_temp}°C")
                        elif current_temp != last_temp:
                            # Температура изменилась
                            msg = f"🌡 Температура изменилась! Было: {last_temp}°C, стало: {current_temp}°C"
                            bot.send_message(user_id, msg)
                            last_temp = current_temp
            except Exception as e:
                print(f"Ошибка при запросе: {e}")
        
        time.sleep(5) # Интервал 5 секунд

# Запуск фонового потока для мониторинга
monitor_thread = Thread(target=monitoring_loop, daemon=True)
monitor_thread.start()

# Главное меню с кнопками Старт / Стоп
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = types.KeyboardButton('🟢 Старт')
    btn_stop = types.KeyboardButton('🔴 Стоп')
    markup.add(btn_start, btn_stop)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    global user_id
    user_id = message.chat.id
    bot.send_message(
        user_id, 
        "Привет! Я бот мониторинга температуры UUWW (Внуково).\nИспользуй кнопки ниже для управления.", 
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global is_running, last_temp, user_id
    user_id = message.chat.id

    if message.text == '🟢 Старт':
        if not is_running:
            is_running = True
            bot.send_message(user_id, "Включаю мониторинг...", reply_markup=get_main_keyboard())
        else:
            bot.send_message(user_id, "Мониторинг уже работает.", reply_markup=get_main_keyboard())

    elif message.text == '🔴 Стоп':
        if is_running:
            is_running = False
            last_temp = None # Сбрасываем, чтобы при следующем старте актуализировать
            bot.send_message(user_id, "Мониторинг остановлен.", reply_markup=get_main_keyboard())
        else:
            bot.send_message(user_id, "Мониторинг и так выключен.", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    print("Бот успешно запущен локально...")
    bot.infinity_polling()
