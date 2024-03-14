import datetime
import json
import os

import requests
import telebot
from dotenv import load_dotenv
from telebot.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton,
                           ReplyKeyboardMarkup,
                           KeyboardButton)

# Загрузка переменных окруженияиз dot-env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
# Получение токенов из dotenv
BOT_TOKEN = os.getenv('BOT_TOKEN')
GIPHY_TOKEN = os.getenv('GIPHY_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
WEATHER_KEY = os.getenv('WEATHER_KEY')
# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['newsletter'])
def input_newsletter(message):
    """
    Возможности админа: введя эту команду, можно запустить рассылку следующего введенного сообщения
    """
    # Проверка на админа
    if str(message.chat.id) == str(ADMIN_ID):
        bot.send_message(message.chat.id, "Введите текст рассылки:")
        bot.register_next_step_handler(message, send_newsletter)
    else:
        bot.send_message(message.chat.id, 'Извините, я не понимаю эту команду.')


@bot.message_handler(commands=['start'])
def start(message):
    """
    Стартовая функция, которая начинает работу при начале общения пользователя и бота
    """
    # запись id чата в файл (Пригодится для рассылок)
    with open("users.txt", "a") as file:
        if str(message.chat.id) not in open("users.txt", "r").read():
            file.write(str(message.chat.id) + "\n")
    # Создание клавиатуры и добавление кнопок
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("Оставить заявку"), KeyboardButton("Оставить отзыв"))
    markup.row(KeyboardButton("Посмотреть отзывы"))
    # Приветственная отбивка
    bot.send_message(message.chat.id, "Добрый день! Как я могу вам помочь?", reply_markup=markup)


@bot.message_handler(commands=['help'])
def helping(message):
    """
    Запускается при команде /help. Выводит основную информацию о боте
    """
    bot.send_message(message.chat.id, '/start - запуск бота\n/help - ' 
                                      'Сообщение с помощью\n"Оставить заявку" - для перехода к спискам услуг\n'
                                      '"Оставить отзыв" - если вы хотите оставить обратную связь\n'
                                      '"Посмотреть отзывы" - если вы хотите просмотреть ранее оставленные отзывы об услугах')


@bot.message_handler(func=lambda message: message.text == "Оставить заявку")
def handle_leave_request(message):
    """
    Запускается при нажатии кнопки Оставить заявку или ввода сообщения.
    Выводит сообщения с inline кнопками для выбора услуг
    """
    keyboard = InlineKeyboardMarkup()
    # Добавление кнопок к inline клавиатуре
    keyboard.row(
        InlineKeyboardButton("Услуга 1", callback_data="Услуга 1"),
        InlineKeyboardButton("Услуга 2", callback_data="Услуга 2"),
        InlineKeyboardButton("Услуга 3", callback_data="Услуга 3"))
    # Сообщение с кнопками
    bot.send_message(message.chat.id, "Выберите услугу:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "Оставить отзыв")
def review_handler(message):
    """
    Запускается при нажатии кнопки Оставить отзыв или ввода сообщения.
    Выводит сообщение и запускает функцию для сохранения отзыва.
    """
    bot.send_message(message.chat.id, "Пожалуйста, введите ваш отзыв:")
    # Перевод на следующую функцию
    bot.register_next_step_handler(message, lambda message: save_input(message, type='reviews'))


@bot.callback_query_handler(func=lambda call: call.data.startswith("Услуга"))
def handle_service_selection(call):
    """
    Запускается, если переданные данные содержат значение: услуга.
    Союбирает имя пользователя, после чего переводит на следующий этап
    """
    service = call.data
    bot.send_message(call.message.chat.id, "Введите ваше имя:")
    bot.register_next_step_handler(call.message, lambda message: ask_contact(message, service))


@bot.message_handler(func=lambda message: message.text == "Посмотреть отзывы")
def show_reviews(message):
    """
    Запускается при нажатии кнопки Оставить заявку или ввода сообщения.
    Считывает отзывы из файла и выводит уникальные для пользователя отзывы
    """
    # Открытие файла и запись его в словарь
    try:
        with open("reviews.json", "r") as file:
            reviews = json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        reviews = {}
    # Проверка, что пользователь оставлял отзывы
    if str(message.chat.id) in reviews:
        bot.send_message(message.chat.id, "Ваши отзывы:")
        # проход по словарю и вывод отформатированных отзывов
        for review in reviews[str(message.chat.id)]:
            date = review["date"].split()[0]
            text = review["text"]
            bot.send_message(message.chat.id, f"Дата: {date}\nОтзыв: {text}")
    else:
        bot.send_message(message.chat.id, "У вас пока нет отзывов.")


@bot.message_handler(func=lambda message: message.text in 'ПриветЗдравствуйтеHello')
def handle_message(message):
    """
    Элемент человечности. Реагирует на приветствие
    """
    bot.send_message(message.chat.id, "Здравствуйте! чем я могу вам помочь?")


@bot.message_handler(func=lambda message: message.text == 'ПокаДо свиданияBye')
def handle_message(message):
    """
    Элемент человечности. Реагирует на прощание
    """
    bot.send_message(message.chat.id, "До свидания! Надеюсь мои услуги оказались вам полезны.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Отбивка для рандомных сообщений пользователя
    """
    bot.send_message(message.chat.id, "Извините, я не понимаю эту команду.")


def ask_contact(message, service):
    """
    Следующий после сбора имени этап сбора заявки.
    Собирает контакт и начинает процесс сохранения заявки в файле
    """
    name = message.text
    bot.send_message(message.chat.id, "Введите ваш контакт (номер телефона, email и т.д.):")
    bot.register_next_step_handler(message,
                                   lambda message: save_input(message, name=name, service=service, type='requests'))


def save_input(message, **kwargs):
    """
    Функция сохранения введенных пользователем данных в файл. Работает как с заявками, так и с отзывами.
    """
    from_file = {}
    # Чтение данных из файла и запись в словарь
    with open(f"{kwargs.get("type")}.json", "r", encoding='utf-8') as file:
        from_file = json.load(file)
    chat_id = message.from_user.id
    # В зависимости от типа ввода, сообщение формируется по разному
    if kwargs.get("type") == "reviews":
        data = {"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "text": message.text}
    else:
        data = {"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": kwargs.get('name'),
                "contact": message.text,
                "service": kwargs.get('service'),
                }
    # Проверка на то, что пользователь оставлял отзывы или заявки
    if str(chat_id) in from_file:
        from_file[str(chat_id)].append(data)
    else:
        from_file[str(chat_id)] = [data]
    # Открытие файла на запись и запись в файл
    with open(f"{kwargs.get("type")}.json", "w", encoding='utf-8') as file:
        json.dump(from_file, file, indent=4)
    # Различная отбивка в зависимости от типа ввода
    if kwargs.get("type") == "requests":
        bot.send_message(chat_id, f"Спасибо за вашу заявку! С вами скоро свяжется менеджер для уточнения деталей.")
        bot.send_animation(message.chat.id, get_gif('Спасибо!'))
    else:
        bot.send_message(chat_id, f"Спасибо за ваш отзыв!")
        bot.send_animation(message.chat.id, get_gif('Спасибо!'))


def send_newsletter(message):
    """
    Вспомогательная функция для рассылки сообщений.
    Проходится по сохраненным id чатов и рассылает введенное админом сообщение
    """
    with open("users.txt", "r") as file:
        chat_ids = file.readlines()
    # Проход по id
    for chat_id in chat_ids:
        chat_id = chat_id.strip()
        bot.send_message(chat_id, message.text)


def get_gif(name):
    """
    Вспомогательная функция для получение гифки через API GIPHY
    """
    url = "http://api.giphy.com/v1/gifs/search"
    # Параметры для request
    param = {
        "api_key": GIPHY_TOKEN,
        "rating": "g",
        "q": name,
        "limit": 1,
        "lang": "ru"
    }
    # получение данных
    result = requests.get(url, params=param).json()
    # Вытаскивание ссылки на необходимую гифку
    link_origin = result["data"][0]["images"]["original"]["url"]
    return link_origin


if __name__ == '__main__':
    bot.infinity_polling()
