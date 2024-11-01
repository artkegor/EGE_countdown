import os
import time

import db
import dotenv

import telebot
import schedule
import threading
from telebot import types
from datetime import datetime

# Конфигурация бота
dotenv.load_dotenv()
TOKEN = os.getenv('TOKEN')
ADMIN = int(os.getenv('ADMIN'))

bot = telebot.TeleBot(TOKEN)

# Данные для кнопок
subject_buttons = {
    'rus': ('Русский 📕', 'sub_rus'),
    'mat': ('Математика 📘', 'sub_mat'),
    'his': ('История 🏰', 'sub_his'),
    'lit': ('Литература 📖', 'sub_lit'),
    'obs': ('Обществознание 🧑‍⚖️', 'sub_obs'),
    'fiz': ('Физика 🚀', 'sub_fiz'),
    'inf': ('Информатика 💻', 'sub_inf'),
    'him': ('Химия 🧪', 'sub_him'),
    'bio': ('Биология 🐭', 'sub_bio'),
    'geo': ('География 🗺', 'sub_geo'),
    'lan': ('Иностранные языки 🌍', 'sub_lan'),
}

# Даты экзаменов
exam_dates = {
    "rus": datetime(2025, 5, 30),
    "mat": datetime(2025, 5, 27),
    "his": datetime(2025, 5, 23),
    "lit": datetime(2025, 5, 23),
    "obs": datetime(2025, 6, 2),
    "fiz": datetime(2025, 6, 2),
    "inf": datetime(2025, 6, 10),
    "him": datetime(2025, 5, 23),
    "bio": datetime(2025, 6, 5),
    "geo": datetime(2025, 6, 5),
    "lan": datetime(2025, 6, 5)
}


# Клавиатура с предметами
def subjects_markup(subjects):
    active_subjects = {subject['name'] for subject in subjects if subject['active']}

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            f"{subject_buttons['rus'][0]} ✅" if 'rus' in active_subjects else subject_buttons['rus'][0],
            callback_data=subject_buttons['rus'][1]
        ),
        types.InlineKeyboardButton(
            f"{subject_buttons['mat'][0]} ✅" if 'mat' in active_subjects else subject_buttons['mat'][0],
            callback_data=subject_buttons['mat'][1]
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            f"{subject_buttons['his'][0]} ✅" if 'his' in active_subjects else subject_buttons['his'][0],
            callback_data=subject_buttons['his'][1]
        ),
        types.InlineKeyboardButton(
            f"{subject_buttons['lit'][0]} ✅" if 'lit' in active_subjects else subject_buttons['lit'][0],
            callback_data=subject_buttons['lit'][1]
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            f"{subject_buttons['obs'][0]} ✅" if 'obs' in active_subjects else subject_buttons['obs'][0],
            callback_data=subject_buttons['obs'][1]
        ),
        types.InlineKeyboardButton(
            f"{subject_buttons['fiz'][0]} ✅" if 'fiz' in active_subjects else subject_buttons['fiz'][0],
            callback_data=subject_buttons['fiz'][1]
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            f"{subject_buttons['inf'][0]} ✅" if 'inf' in active_subjects else subject_buttons['inf'][0],
            callback_data=subject_buttons['inf'][1]
        ),
        types.InlineKeyboardButton(
            f"{subject_buttons['him'][0]} ✅" if 'him' in active_subjects else subject_buttons['him'][0],
            callback_data=subject_buttons['him'][1]
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            f"{subject_buttons['bio'][0]} ✅" if 'bio' in active_subjects else subject_buttons['bio'][0],
            callback_data=subject_buttons['bio'][1]
        ),
        types.InlineKeyboardButton(
            f"{subject_buttons['geo'][0]} ✅" if 'geo' in active_subjects else subject_buttons['geo'][0],
            callback_data=subject_buttons['geo'][1]
        )
    )

    markup.add(types.InlineKeyboardButton(
        f"{subject_buttons['lan'][0]} ✅" if 'lan' in active_subjects else subject_buttons['lan'][0],
        callback_data=subject_buttons['lan'][1]))

    markup.add(types.InlineKeyboardButton('Готово ✅', callback_data='done'))

    return markup


# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    if not db.get_user(message.chat.id):
        db.add_user(message.chat.id)

    subjects = db.get_subjects(message.chat.id)
    markup = subjects_markup(subjects)

    bot.send_message(message.chat.id, 'Привет!\n'
                                      'Выбери предметы, которые ты сдаешь...', reply_markup=markup)


# Обрабатываем нажатия кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith('sub_'):
        subject = call.data.split('_')[1]
        db.add_subject(call.message.chat.id, subject)

        subjects = db.get_subjects(call.message.chat.id)
        markup = subjects_markup(subjects)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Привет!\n'
                                   'Выбери предметы, которые ты сдаешь...',
                              reply_markup=markup)

    elif call.data == 'done':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Изменить предметы ✏️', callback_data='change'))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Теперь ровно в полночь ты будешь получать уведомление с количеством дней до экзаменов.\n\n'
                                   'Удачи в подготовке!', reply_markup=markup)
    elif call.data == 'change':
        subjects = db.get_subjects(call.message.chat.id)
        markup = subjects_markup(subjects)

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Привет!\n'
                                   'Выбери предметы, которые ты сдаешь...', reply_markup=markup)


# Рассылка
def send_daily():
    users = db.get_all_users()
    for user in users:
        time.sleep(0.1)
        try:
            subjects = user['subjects']
            if subjects:
                message = '<b>Дней до экзаменов:</b>\n\n'
                for subject in subjects:
                    exam_date = exam_dates[subject['name']]
                    days_till_exam = (exam_date - datetime.now()).days
                    message += f'{subject_buttons[subject["name"]][0]}: {days_till_exam} дней.\n\n'
                bot.send_message(user['id'], message, parse_mode='html')
        except:
            continue


# Планируем отправку в 12 ночи
schedule.every().day.at("00:00").do(send_daily)


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


threading.Thread(target=run_schedule, daemon=True).start()


# Команда для админа
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.chat.id == ADMIN:
        bot.send_message(message.chat.id, f'Количество пользователей: {db.count_users()}')


bot.infinity_polling()
