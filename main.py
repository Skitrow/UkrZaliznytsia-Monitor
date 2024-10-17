import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import datetime
import json




API = "7346037417:AAEnmS-Zw7MUacyqmokPmDomVpYLFV9g2Kw"
bot = telebot.TeleBot(API)

users_data = {}

def get_request(date, bearer, station_from, station_to):
    print(bearer)
    print(type(bearer))
    try:
        url = f"https://app.uz.gov.ua/api/v3/trips?station_from_id={station_from}&station_to_id={station_to}&with_transfers=0&date={date}"
        r = requests.request("GET", url
                             ,
                             headers={"User-Agent": "UZ/2.0.5 Android/7.1.2 User/266639", "Authorization": f"Bearer {bearer}"})
        return r
    except Exception as e:
        print(e)
        time.sleep(5)
        get_request(date)


def get_station_id(station_name):
    r = requests.request("GET", "https://app.uz.gov.ua/api/stations?search=",
                         headers={"User-Agent": "UZ/2.0.5 Android/7.1.2 User/266639"}).json()

    for i in r:
        if i['name'] == station_name:
            return i['id']


def parse(date, train, clas, req, chat_id):
    r = req


    if r.status_code == 200:
        # print(type(r.json()['direct'])
        for i in r.json()['direct']:
            if i['train']['number'] == train:
                for j in i['train']['wagon_classes']:
                    print(f"{datetime.datetime.now()} {i['train']['number']} {j['id']} {j}")
                    bot.send_message(int(chat_id),
                                     f"{datetime.datetime.now()} {i['train']['number']} {j['id']} {j}")
                    if j['id'] == clas and j['free_seats'] != 0:
                        bot.send_message(int(chat_id),
                                         f"З'явилось місце на {date} у {train}. Всього місць: {j['free_seats']}. https://booking-new.uz.gov.ua/trips/{i['id']}?classId={j['id']}")



    else:
        bot.send_message(524589401, 'Failed status code')
        print(r.status_code)


@bot.message_handler(commands=['start'])
def start(message):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('Авторизація'))
    sent = bot.send_message(message.chat.id, f'Вітаю, {message.from_user.first_name} \nОберіть варіант: ',
                                    reply_markup=markup)
    bot.register_next_step_handler(sent, authorisation_button)
    print("Пройдіть авторизацію у боті")
    # markup = ReplyKeyboardMarkup(resize_keyboard=True)
    # markup.add(KeyboardButton('Добавити рейс'))
    # markup.add(KeyboardButton('Переглянути мої рейси'))
    # bot.send_message(message.chat.id, "Ви успішно авторизовані!", reply_markup=markup)
    # bot.send_message(message.chat.id, 'Моніторинг включено')


    # while True:
    #     for d in ['2024-10-20']:
    #         r = get_request(d)
    #         for t in ['715К']:
    #             for c in ['С2']:
    #                 parse(d, t, c, r)
    #
    #     time.sleep(60)


def authorisation_button(message):
    if message.text == "Авторизація":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('Назад'))
        sent = bot.send_message(message.chat.id, "Введіть ваш номер телефону(+38000000000):", reply_markup=markup)
        bot.register_next_step_handler(sent, send_number)


def send_number(message):
    if message.text.split('380')[0] == '+':
        phone_number = message.text
        request = requests.request("POST", "https://app.uz.gov.ua/api/auth/send-sms",
                                            headers={"User-Agent": "UZ/2.0.5 Android/7.1.2 User/guest"},
                                            json={"phone": phone_number})
        bot.send_message(message.chat.id, request.text)
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('Назад'))
        sent = bot.send_message(message.chat.id, "Введіть код, отриманий в смс:")

        bot.register_next_step_handler(sent, lambda m: send_code(m, phone_number))


def send_code(message, phone_number):
    if len(message.text) == 4:
        code = message.text
        request = requests.request("POST", "https://app.uz.gov.ua/api/v2/auth/login",
                                         headers={"User-Agent": "UZ/2.0.5 Android/7.1.2 User/guest"},
                                         json={"code": code, "device": {"fcm_token": "", "name": "iphone"},
                                               "phone": phone_number})
        bearer = request.json()['token']['access_token']
        users_data.update({message.chat.id: {"phone_number": phone_number, "Bearer": bearer}})
        if bearer:
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton('Добавити рейс'))
            markup.add(KeyboardButton('Переглянути мої рейси'))
            bot.send_message(message.chat.id, "Ви успішно авторизовані!", reply_markup=markup)
            start_monitor(bearer, message.chat.id)


def start_monitor(bearer, chat_id):
    dates = ['2024-10-20'] # Дата рейсу
    trains = ['715К'] # Номер потягу. Наприклад: 700К
    seat_class = ['С2'] # Клас сидіння. Плацкарт - П, Купе - К, 1 клас - С1, 2 клас - С2
    station_from = get_station_id("Львів") # Станція відправлення
    station_to = get_station_id("Вінниця") # Станція прибуття
    while True:
        for d in dates:
            r = get_request(d, bearer, station_from, station_to)
            for t in trains:
                for c in seat_class:
                    parse(d, t, c, r, chat_id)

        time.sleep(60)



if __name__ == '__main__':
    # with open("users_data.json", "r") as file:
    #     try:
    #         users_data = json.load(file)
    #     except Exception as e:
    #         print(e)
    #         pass

    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    # with open('users_data.json', 'w') as file:
    #     json.dump(users_data, file)










