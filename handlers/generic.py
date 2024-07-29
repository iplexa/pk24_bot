from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

import utils


# Реакция на /start
def response_to_start(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('/register'))
    
    bot.send_message(message.chat.id, f'Добрый день, {message.from_user.first_name}.\nПройдите регистрацию сотрудника при помощи команды /register в формате <code>/register Иван Иванов</code>.', reply_markup=rmk)


# Функция регистрации сотрудника, реакция на команду /register
def register_get_department(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('FrontLine'), KeyboardButton('CallCentre'))
    rmk.add(KeyboardButton('ОТК'), KeyboardButton('Онлайн-заявления'))
    rmk.add(KeyboardButton('Администрация'), KeyboardButton('Ресепшн'))

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберете Ваш отдел.', reply_markup=rmk),
        reg_get_data, bot=bot
    )


def reg_get_data(message: Message, bot: TeleBot):
    department = message.text

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите Ваше имя и фамилию'),
        reg_process, bot=bot, department=department
    )


def reg_process(message: Message, bot: TeleBot, department):
    # Получаем имя, фамилию и отдел из сообщения
    employee_data = utils.is_correct_person_name(name = message.text, middlename_needed = False)

    if len(employee_data) == 1:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы указали неплоные данные.\nКорректный формат: <code>Иван Иванов</code>'), 
            reg_process, bot=bot, department=department
        )
        return
    else:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'))

        if bot.db.register_employee(message.from_user.id, *employee_data, department):
            bot.send_message(message.chat.id, 'Вы успешно зарегистрированы!\nЖелаем хорошей работы :)\n\nЧтобы получить информацию о доступных командах, нажмите на кнопку ниже.', reply_markup=rmk)
        else:
            employee = bot.db.get_employee_data(message.from_user.id)
            bot.send_message(message.chat.id, 'Вы уже зарегистрированы!', reply_markup=rmk)
            
            bot.send_warn(f'Пользователь {message.from_user.username} попытался зарегистрироваться второй раз.\nВ БД значится как: {employee["name"]} {employee["surname"]}.\nОбратиться: @{message.from_user.username}')


def information(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Начать рабочий день'), KeyboardButton('Завершить рабочий день'))
    rmk.add(KeyboardButton('Отправить заявление'), KeyboardButton('Проверить дело'))
    rmk.add(KeyboardButton('Найти заявление'), KeyboardButton('Внести аттестат'))
    rmk.add(KeyboardButton('Заполнить график'), KeyboardButton('Посмотреть график'))


    message_text = '<b>Список команд:</b>\n\n/register — ✅ Пройти регистрацию сотрудника приемной комиссии.\n'
    message_text += 'Отправить заявление — ➡️ Отправить информацию о заявлении абитуриента.\nНайти заявление — ❓ Получить информацию о статусе заявлении абитуриента.\n'
    message_text += 'Внести аттестат — 📕 Отправить информацию о наличии оригинала аттестата.'
    
    bot.send_message(message.chat.id, message_text, reply_markup=rmk)
