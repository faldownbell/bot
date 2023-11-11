import json
import re

from telebot import types
import telebot
import psycopg2
from config import host, user, password, db_name

bot_token = '6879306423:AAF2JWMbRQbB69Ux-vMuipZD_Zk0xpvLQco'
bot = telebot.TeleBot(bot_token)

connection = psycopg2.connect(host=host, user=user, password=password, database=db_name)
cursor = connection.cursor()


def show_options(user_id):
    query = f"SELECT options FROM data_of WHERE user_id = '{user_id}';"
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        json_data = row[0]
        json_obj = json_data

        markup = types.ReplyKeyboardMarkup(row_width=2)

        for key in json_obj:
            button = types.KeyboardButton(key)
            markup.add(button)

        bot.send_message(user_id, "Выберите опцию:", reply_markup=markup)


@bot.message_handler(commands=['start'])
def starter(message):
    global counter
    user_id = message.chat.id
    print("Мой id: {}".format(user_id))
    try:
        query = f"INSERT INTO data_of (user_id, options) VALUES ({user_id}, '{{\"Обучение\": 0, \"Физнагрузки\": 0}}'::json) ON CONFLICT (user_id) DO NOTHING;"
        cursor.execute(query)
        connection.commit()  # Важно завершить транзакцию

        if cursor.rowcount > 0:
            # Если была выполнена вставка (новый пользователь), показываем опции
            show_options(user_id)
        else:
            # Если пользователь уже существует, отправляем сообщение
            bot.send_message(user_id, "Вы уже зарегистрированы")
    except Exception as ex:
        connection.rollback()  # Откатываем транзакцию в случае ошибки
        print(f"Error: {ex}")



@bot.message_handler(commands=['menu'])
def starter(message):
    user_id = message.chat.id
    print("Мой id: {}".format(user_id))
    show_options(user_id)


# Обработчик нажатий на кнопки
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.chat.id

    query = f"SELECT options FROM data_of WHERE user_id = '{user_id}';"
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        json_data = row[0]
        json_obj = json_data

        if message.text in json_obj:
            value = json_obj[message.text]
            bot.send_message(user_id, f"Текущее значение для {message.text}: {value}")
            query = f"UPDATE data_of SET data = '{message.text}' WHERE user_id = '{user_id}';"
            cursor.execute(query)
        else:
            new_value = message.text
            query = f"SELECT data FROM data_of WHERE user_id = {user_id};"
            cursor.execute(query)
            result = cursor.fetchone()
            key_to_change = result[0]
            print(key_to_change)

            query = f"SELECT options FROM data_of WHERE user_id = '{user_id}';"
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                json_data = row[0]
                json_obj = json_data
                if key_to_change in json_obj:
                    json_obj[key_to_change] = new_value
                    updated_json = json.dumps(json_obj)
                    query = f"UPDATE data_of SET options = '{updated_json}' WHERE user_id = '{user_id}';"
                    cursor.execute(query)
                    connection.commit()
                    bot.send_message(user_id, f"Значение для {key_to_change} обновлено успешно: {new_value}")
                    show_options(user_id)
                else:
                    bot.send_message(user_id, "Не удалось определить опцию для изменения.")
                    show_options(user_id)


# Запускаем бота
bot.polling(none_stop=True)
