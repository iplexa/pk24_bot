from datetime import datetime, timedelta

from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from time import sleep
from random import choice

import utils

from constants import GENERIC_CHAT, ADMIN_CHAT, TIME_THREAD_ID

HEART = '🤍'
COLORED_HEARTS = ['💗', '💓', '💖', '💘', '❤️', '💞']
EDIT_DELAY = 0.35

PARADE_MAP = '''
00000000000
00111011100
01111111110
01111111110
00111111100
00011111000
00001110000
00000100000
'''


# Функция начала рабочего дня
def start_workday(message: Message, bot: TeleBot):
    employee = bot.db.get_employee_data(employee_id=message.from_user.id)

    if employee is None:
        bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы не зарегистрированы.\nПожалуйста, пройдите регистрацю с помощью команды /register.')
        return

    start_work_time_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'))

    if bot.db.start_employee_work(employee_id=employee['id'], start_time=message.date):
        bot.send_message(message.chat.id, '<b>Успешное начало рабочего дня!</b>\nЖелаем хорошей работы :)', reply_markup=rmk)
        if message.from_user.id == 1003384470:
            bot.send_message(message.chat.id, 'Солнышко, я не устану повторять, что сегодня ты просто прекрсна!\nОчень надеюсь, что сегодня все будет хорошо и моему котику не за что будет переживать!\nПусть этот день станет одним из лучших в жизни, самая любимая зайка!')
            bot.send_message(message.chat.id, 'Мы справимся со всеми пробемами, даже с самыми невозможными на первый взгляд')
            sleep(0.5)
            bot.send_message(message.chat.id, 'Я всегда рядом, помни об этом')
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEG7JJmlZOkkPtkv8_dxmAbCZ3Wgrxr6QAC1hQAAqaDKEgzjAPyAnBezDUE')
            heart(message=message, bot=bot)
        bot.send_message(chat_id=GENERIC_CHAT, text=f'<code>[{start_work_time_str}]</code>\n▶️▶️▶️\nСотрудник приемной комиссии <b>{employee["name"]} {employee["surname"]}</b> из отдела <b>{employee["department"]}</b> начал рабочий день.', message_thread_id=TIME_THREAD_ID)
    else:
        bot.send_warn(f'Сотрудник {employee["name"]} {employee["surname"]} попытался второй раз начать рабочий день.\nОбратиться: @{message.from_user.username}')
        bot.send_message(message.chat.id, '<b>Вы уже начали рабочий день!</b>\nПри ошбочном начале рабочего дня обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk)

# Богдан, прошу прощения, я потом это уберу от сюда :)

def heart(message: Message, bot: TeleBot):
    msg = bot.send_message(message.chat.id, 'magic')
    process_build_place(message=message, bot=bot, msg=msg)
    process_colored_parade(message=message, bot=bot, msg=msg)
    process_love_words(message=message, bot=bot, msg=msg)
    bot.sen

def generate_parade_colored():
    output = ''
    for c in PARADE_MAP:
        if c == '0':
            output += HEART
        elif c == '1':
            output += choice(COLORED_HEARTS)
        else:
            output += c
    return output


def process_love_words(message: Message, bot: TeleBot, msg: Message):
    bot.edit_message_text(chat_id = message.chat.id, message_id=msg.id, text='Я')
    sleep(1)
    bot.edit_message_text(chat_id = message.chat.id, message_id=msg.id, text='Я очень')
    sleep(1)
    bot.edit_message_text(chat_id = message.chat.id, message_id=msg.id, text='Я очень сильно')
    sleep(1)
    bot.edit_message_text(chat_id = message.chat.id, message_id=msg.id, text='Я очень сильно тебя люблю')
    sleep(1)
    bot.edit_message_text(chat_id = message.chat.id, message_id=msg.id, text='Я очень сильно тебя люблю💗')


def process_build_place(message: Message, bot: TeleBot, msg: Message):
    output = ''
    for i in range(8):
        output += '\n'
        for j in range(11):
            output += HEART
            bot.edit_message_text(chat_id = message.chat.id, message_id=msg.id, text=output)
            sleep(EDIT_DELAY / 2)


def process_colored_parade(message: Message, bot: TeleBot, msg: Message):
    for i in range(50):
        text = generate_parade_colored()
        bot.edit_message_text(chat_id = message.chat.id, message_id=msg.id, text=text)
        sleep(EDIT_DELAY)






# Функция окончания рабочего дня
def end_workday(message: Message, bot: TeleBot):
    employee = bot.db.get_employee_data(employee_id=message.from_user.id)
    
    if employee is None:
        # Сделать универсальную функцию
        bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы не зарегистрированы.\nПожалуйста, пройдите регистрацю с помощью команды /register.')
        return
    
    end_work_time_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'))

    result, start_work, end_work = bot.db.end_employee_work(employee_id=employee['id'], end_time=message.date)

    if result:
        time_worked = end_work - start_work.timestamp()
        time_worked_str = utils.seconds_to_simple_time_str(seconds=time_worked)

        start_time_str = start_work.strftime("%H:%M")
        end_time_str = datetime.fromtimestamp(end_work).strftime("%H:%M")
        workday_str = datetime.fromtimestamp(end_work).strftime('%d.%m.%Y')
        workday = datetime.strptime(workday_str, '%d.%m.%Y')

        employee_schedule = bot.db.get_employee_schedule_information(
            employee_id=message.from_user.id, 
            workday=workday
        )

        if employee_schedule:
            overwork = time_worked - (employee_schedule['end_datetime'] - employee_schedule['start_datetime'])
            if overwork < 0:
                overwork_str = '-' + utils.seconds_to_simple_time_str(seconds=abs(overwork))
            else:
                overwork_str = utils.seconds_to_simple_time_str(seconds=overwork)
            
            if overwork > 5400:
                bot.send_warn(f'У Сотрудниа {employee["name"]} {employee["surname"]} слишком большая переработка!\nПереработка: {overwork_str}\nСвязь с сотрудником: @{message.from_user.username}')
        else:
            overwork_str = 'График сотрудника не заполнен.'
        
        message_str = f'<code>[{end_work_time_str}]</code>\n⏸️⏸️⏸️\nСотрудник приемной комиссии <b>{employee["name"]} {employee["surname"]}</b> из отдела <b>{employee["department"]}</b> закончил рабочий день.\n'
        message_str += f'Отработал {time_worked_str} с {start_time_str} по {end_time_str}.\n'
        message_str += f'Переработка: {overwork_str}'        

        bot.send_message(message.chat.id, '<b>Успешное завершение рабочего дня!</b>\nХорошего Вам отдыха!', reply_markup=rmk)
        if message.from_user.id == 1003384470:
            bot.send_message(message.chat.id, 'Котик мой, хорошо отдохнуть тебе сегодня💗\nЛюблю тебя и уже очень скучаю💞')
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEGzhZmjqkDTG0SI7eiuK-6d0hVnrbcaAACFxgAAuB6sEsLI4xbCA9hUzUE')
            sleep(0.5)
            bot.send_message(message.chat.id, 'Никогда не сомневайся в себе\nТы умничка, у тебя все получится')
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAEG3LpmkmdNT5IKhuDN01UPaCEZcghyugACvBcAAtWMIUnoFSL1_p3OXDUE')
            
        bot.send_message(GENERIC_CHAT, message_str, message_thread_id=TIME_THREAD_ID)

    else:
        bot.send_message(message.chat.id, '<b>Вы уже завершили рабочий день!</b>\nПри ошбочном завершении рабочего дня обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>')
        bot.send_warn(f'Сотрудник {employee["name"]} {employee["surname"]} попытался второй раз завершить рабочий день.\nОбратиться: @{message.from_user.username}')


def fill_schedule(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Текущая неделя'), KeyboardButton('Следующая неделя'))
    rmk.add(KeyboardButton('Отмена'))
    if message.text == 'Заполнить график':
        bot.send_message(message.chat.id, '🔸 Вы начали процесс заполнения графика.')
        admin = False, ''
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите дату начала рабочей недели в формате DD.MM, или выберите из предложенных варинатов.\nУчтите, что дата начала рабочей недели - понедельник.\n<code>Например, 08.07.</code>', reply_markup=rmk),
            fill_schedule_get_date,
            employee_id = message.from_user.id,
            admin = admin,
            bot=bot
        )
    else:
        employee = bot.db.get_employee_data_via_fullname(employee_fullname=message.text)
        bot.send_message(message.chat.id, '🔸 Вы начали процесс заполнения графика за сотрудника.')
        admin = True, message.from_user.id 
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите дату начала рабочей недели в формате DD.MM, или выберите из предложенных варинатов.\nУчтите, что дата начала рабочей недели - понедельник.\n<code>Например, 08.07.</code>', reply_markup=rmk),
            fill_schedule_get_date,
            employee_id = employee['id'],
            admin = admin,
            bot=bot
        )


def fill_schedule_get_date(message: Message, employee_id: int, admin, bot: TeleBot):
    date_start_str = message.text
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('9:00 - 15:00'), KeyboardButton('10:00 - 16:00'))
    rmk.add(KeyboardButton('9:00 - 16:00'), KeyboardButton('10:00 - 17:00'))
    rmk.add(KeyboardButton('11:00 - 18:00'), KeyboardButton('9:00 - 18:00'))
    rmk.add(KeyboardButton('Отмена'))
    last_workday = bot.db.get_last_employee_workday_in_schedule(employee_id=employee_id)
    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if admin[0]:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))
        else:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график'))
        bot.send_message(message.chat.id, 'Процесс заполнения графика остановлен.', reply_markup=rmk)
        return
    if date_start_str in ['Текущая неделя', 'Следующая неделя']:
        date_start = utils.get_week_date(period=date_start_str)
    elif utils.check_date_format(date_start_str):
        date_start = datetime.strptime(date_start_str + ".2024", "%d.%m.%Y")
    else: 
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы неверно указали дату.\nВведите дату начала рабочей недели в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\nНапример, <code>Например, 08.07.</code>', reply_markup=rmk),
            fill_schedule_get_date,
            employee_id = employee_id, admin=admin, bot=bot
        )
        return
    if date_start.weekday() != 0:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Выбранная Вами дата не является понедельником.\nВведите дату начала рабочей недели в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\nНапример, <code>Например, 08.07.</code>'),
            fill_schedule_get_date,
            employee_id = employee_id, admin = admin, bot=bot
        )
        return
    if last_workday is not None and last_workday["end_datetime"] > date_start.timestamp():
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if admin[0]:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))
            bot.send_message(message.chat.id, '<b>Сотдруник уже заполнили свой график на эту неделю!</b>\nПри ошибочном заполнении графика, а также при сбоях в работе обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
        else:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график'))
            bot.send_message(message.chat.id, '<b>Вы уже заполнили свой график на эту неделю!</b>\nПри ошибочном заполнении графика, а также при сбоях в работе обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
        return
    
    
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите время начала и окончания рабочего дня, в формате <b>10:00 - 20:00</b>.', reply_markup=rmk),
        fill_schedule_get_time,
        date_start = date_start, employee_id = employee_id, admin = admin, bot=bot
    )

def fill_schedule_get_time(message: Message, date_start: datetime, employee_id: int, admin, bot: TeleBot):
    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if admin[0]:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))
        else:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график'))
        bot.send_message(message.chat.id, 'Процесс заполнения графика остановлен.', reply_markup=rmk)
        return
    worktimelist = utils.parse_time_range(message.text)
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Отмена'))

    if not worktimelist:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы неверно указали рабочее время.\nВведите время начала и окончания рабочего дня, в формате <b>10:00 - 20:00</b>.', reply_markup=rmk),
            fill_schedule_get_time,
            date_start = date_start, employee_id = employee_id, admin=admin, bot=bot
        )
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
    rmk.add(KeyboardButton('Отмена'))

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Сотрудник работает в субботу?' if admin[0] else 'Работаете в субботу?', reply_markup=rmk),
        fill_schedule_get_saturday,
        date_start = date_start, worktimelist = worktimelist, employee_id = employee_id, admin = admin, bot=bot
    )

def fill_schedule_get_saturday(message: Message, date_start: datetime, worktimelist, employee_id: int, admin, bot: TeleBot):
    ans = message.text
    if ans == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if admin[0]:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))
        else:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график'))
        bot.send_message(message.chat.id, 'Процесс заполнения графика остановлен.', reply_markup=rmk)
        return
    if ans == 'Да':
        is_saturday_workday = True
    elif ans == 'Нет':
        is_saturday_workday = False
    else: 
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
        rmk.add(KeyboardButton('Отмена'))

        bot.send_message(message.chat.id, '<b>Ошибка!</b> Выберите вариант ответа из доступных.', reply_markup=rmk),
        fill_schedule_get_time,
        date_start = date_start, worktimelist = worktimelist, employee_id = employee_id, admin = admin
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if admin[0]:
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))
    else:
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график'))
    employee = bot.db.get_employee_data(employee_id=employee_id)

    result = bot.db.fill_schedule(
        employee_id=employee_id,
        start_date=date_start,
        worktime=worktimelist,
        is_saturday=is_saturday_workday
    )
    if result:
        schedule = bot.db.get_employee_schedule_via_startdate(employee_id=employee_id, startdate=date_start)
        start_time_str = datetime.fromtimestamp(schedule[0]["start_datetime"]).strftime('%H:%M')
        end_time_str = datetime.fromtimestamp(schedule[0]["end_datetime"]).strftime('%H:%M')

        bot.send_message(message.chat.id, '<b>График сотрудника успешно заполнен!</b>' if admin[0] else '<b>Ваш график успешно заполнен!</b>', reply_markup=rmk)
        admin_message_text = f'📆 Сотрудник отдела {employee["department"]}, {employee["name"]} {employee["surname"]} заполнил свой график.\n'
        admin_message_text += f'Data: Дата начала: {date_start.strftime("%d.%m.%Y")}, время: {start_time_str} - {end_time_str}\nСотрудник работает в субботу: {"Да" if is_saturday_workday else "Нет"}\n'
        admin_message_text += f'Связь с сотрудником, выполнившим команду: @{message.from_user.username}'
        
        if admin[0]:
            admin_info = bot.db.get_employee_data(employee_id=admin[1])
            admin_message_text += f'\nКоманда была выполнена администратором {admin_info["name"]} {admin_info["surname"]}'
        
        bot.send_message(ADMIN_CHAT, admin_message_text)

        if admin[0]:
            rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Посмотреть график'))
            
            schedule = bot.db.get_employee_schedule_via_startdate(employee_id=employee_id, startdate=date_start)
            
            answer = f'📆 Ваш график на неделю:\n\n'
            for i in schedule:
                date_str = datetime.fromtimestamp(i["start_datetime"]).strftime('%d.%m.%Y')
                start_time_str = datetime.fromtimestamp(i["start_datetime"]).strftime('%H:%M')
                end_time_str = datetime.fromtimestamp(i["end_datetime"]).strftime('%H:%M')
                answer += f'📍 <b>{date_str}</b>: c {start_time_str} до {end_time_str}\n'
            
            bot.send_message(employee_id, f'❕ Администратор <b>{admin_info["name"]} {admin_info["surname"]}</b> заполнил Вам график с {date_start.strftime("%d.%m.%Y")} по {(date_start + timedelta(days=6)).strftime("%d.%m.%Y")}.\n{answer}', reply_markup=rmk)


    else:
        schedule = bot.db.get_employee_schedule_via_startdate(employee_id=employee_id, startdate=date_start)
        start_time_str = datetime.fromtimestamp(schedule[0]["start_datetime"]).strftime('%H:%M')
        end_time_str = datetime.fromtimestamp(schedule[0]["end_datetime"]).strftime('%H:%M')

        bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
        warn_message = f'При попытке сотрудника отдела {employee["department"]}, {employee["name"]} {employee["surname"]} заполнить свой график произошла ошибка.'
        warn_message += f'Data: Дата начала: {date_start.strftime("%d.%m.%Y")}, время: {start_time_str} - {end_time_str}\nСотрудник работает в субботу: {"Да" if is_saturday_workday else "Нет"}\n'
        warn_message += f'Связь с сотрудником, выполнившим команду: @{message.from_user.username}'
        if admin[0]:
            admin_info = bot.db.get_employee_data(employee_id=admin[1])
            warn_message += f'\nКоманда была выполнена администратором {admin_info["name"]} {admin_info["surname"]}'
        bot.send_warn(warn_message)


def see_schedule(message: Message, bot: TeleBot):
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Текущая неделя'), KeyboardButton('Следующая неделя'))
    rmk.add(KeyboardButton('Отмена'))
    if message.text == 'Посмотреть график':
        bot.send_message(message.chat.id, '🔸 Вы начали процесс просмотра графика.')
        admin = False, ''
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите дату начала рабочей недели, за которую хотите просмотреть график, в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\n<code>Например, 08.07.</code>', reply_markup=rmk),
            get_workweek_see_schedule,
            employee_id = message.from_user.id,
            admin = admin,
            bot=bot
        )
    else:
        employee = bot.db.get_employee_data_via_fullname(employee_fullname=message.text)
        bot.send_message(message.chat.id, '🔸 Вы начали процесс просмотра графика сотрудника.')
        admin = True, message.from_user.id 
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите дату начала рабочей недели, за которую хотите просмотреть график сотрудника, в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\n<code>Например, 08.07.</code>', reply_markup=rmk),
            get_workweek_see_schedule,
            employee_id = employee['id'],
            admin = admin,
            bot=bot
        )

def get_workweek_see_schedule(message: Message, employee_id: int, admin, bot: TeleBot):
    date_start_str = message.text
    if date_start_str == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Посмотреть график'))
        bot.send_message(message.chat.id, 'Процесс просмотра графика остановлен.', reply_markup=rmk)
        return
    if date_start_str in ['Текущая неделя', 'Следующая неделя']:
        date_start = utils.get_week_date(period=date_start_str)
    elif utils.check_date_format(date_start_str):
        date_start = datetime.strptime(date_start_str + ".2024", "%d.%m.%Y")
    else: 
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы неверно указали дату.\nВведите дату начала рабочей недели в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\nНапример, <code>Например, 08.07.</code>', reply_markup=rmk),
            get_workweek_see_schedule,
            bot=bot
        )
        return
    if date_start.weekday() != 0:
            bot.register_next_step_handler(
                bot.send_message(message.chat.id, '<b>Ошибка!</b> Выбранная Вами дата не является понедельником.\nВведите дату начала рабочей недели в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\nНапример, <code>Например, 08.07.</code>'),
                get_workweek_see_schedule,
                bot=bot
            )
            return
    schedule = bot.db.get_employee_schedule_via_startdate(employee_id=employee_id, startdate=date_start)
    
    if schedule == []:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if admin[0]:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))
            bot.send_message(message.chat.id, '<b>Сотрудник не заполнил свой график на эту неделю!</b>\nЕсли Вы уже заполнили график, а также при сбоях в работе обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
        else:
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график'))
            bot.send_message(message.chat.id, '<b>Вы не заполнили свой график на эту неделю!</b>\nЕсли Вы уже заполнили график, а также при сбоях в работе обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
        return
        

    answer = f'📆 График сотрудника на неделю:\n\n' if admin[0] else f'📆 Ваш график на неделю:\n\n'
    for i in schedule:
        date_str = datetime.fromtimestamp(i["start_datetime"]).strftime('%d.%m.%Y')
        start_time_str = datetime.fromtimestamp(i["start_datetime"]).strftime('%H:%M')
        end_time_str = datetime.fromtimestamp(i["end_datetime"]).strftime('%H:%M')
        answer += f'📍 <b>{date_str}</b>: c {start_time_str} до {end_time_str}\n'
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if admin[0]:
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Посмотреть график сотрудника'))
    else:
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Посмотреть график'))
    bot.send_message(message.chat.id, answer, reply_markup=rmk)


