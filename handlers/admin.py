from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from time import sleep

import utils

from .schedule import fill_schedule, see_schedule
from constants import ADMIN_CHAT


def admin_menu(message: Message, bot: TeleBot):
    admin = bot.db.is_admin(employee_id=message.from_user.id)
    head = bot.db.is_head(employee_id=message.from_user.id)
    
    if not (admin or head):
        bot.send_message(message.chat.id, '📛 <b>Отказано в доступе!</b>\nДанная команда доступна только администрации!')
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Заполнить график сотрудника'), KeyboardButton('Посмотреть график сотрудника'))
    rmk.add(KeyboardButton('Изменить график сотрудника'), KeyboardButton('Посмотреть заполненные графики'))
    rmk.add(KeyboardButton('Сформировать отчет'))
    rmk.add(KeyboardButton('Сформировать excel'))


    bot.send_message(message.chat.id, '<b>Вы вошли в меню администратора.</b>', reply_markup=rmk)


def admin_fill_and_seeschedule(message: Message, bot: TeleBot):
    admin = bot.db.is_admin(employee_id=message.from_user.id)
    head = bot.db.is_head(employee_id=message.from_user.id)

    if not (admin or head):
        bot.send_message(message.chat.id, '📛 <b>Отказано в доступе!</b>\nДанная команда доступна только администрации!')
        return

    action_schedule = True if message.text == 'Заполнить график сотрудника' else False
    bot.send_message(message.chat.id, f'🔸 Вы начали процесс {"заполнения" if action_schedule else "просмотра"} графика сотрудника.')
    select_department_to_fill_and_see_schedule(employee_id = message.from_user.id, employee_chat_id = message.chat.id, admin=admin, head=head, action_schedule=action_schedule, bot=bot)

def select_department_to_fill_and_see_schedule(employee_id, employee_chat_id, admin, head, action_schedule, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if admin:
        rmk.add(KeyboardButton('FrontLine'), KeyboardButton('CallCentre'))
        rmk.add(KeyboardButton('ОТК'), KeyboardButton('Онлайн-заявления'))
        rmk.add(KeyboardButton('Администрация'), KeyboardButton('Ресепшн'))
    elif head:
        employee = bot.db.get_employee_department(employee_id=employee_id)
        bot.send_message(employee_chat_id, f'Вам {"доступно заполнение" if action_schedule else "доступен просмотр"} графиков сотрудников только своего отдела.')
        rmk.add(KeyboardButton(f'{employee["department"]}'))
        
    rmk.add(KeyboardButton('Отмена'))
    
    bot.register_next_step_handler(
        bot.send_message(employee_chat_id, 'Выберите отдел сотрудника.', reply_markup=rmk),
        select_employee_to_fill_and_see_schedule,
        action_schedule = action_schedule,
        admin=admin, head=head,
        employee_id=employee_id, employee_chat_id=employee_chat_id,
        bot=bot
    )


def select_employee_to_fill_and_see_schedule(message: Message, admin, head, employee_id, employee_chat_id, action_schedule, bot: TeleBot):
    department = message.text

    if department == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton(f'{"Заполнить" if action_schedule else "Посмотреть"} график сотрудника'))
        bot.send_message(employee_chat_id, f'Процесс {"заполнения" if action_schedule else "просмотра"} графика остановлен.', reply_markup=rmk)
        
        return
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    employees = bot.db.get_employees_via_department(employees_department=department)
    
    if not employees:
        bot.send_message(employee_chat_id, '<b>Вы выбрали неправильный отдел!</b>')
        select_department_to_fill_and_see_schedule(employee_id=employee_id, employee_chat_id=employee_chat_id, admin=admin, head=head, action_schedule=action_schedule, bot=bot)
        return
    
    for i in employees:
        rmk.add(KeyboardButton(f'{i["fullname"]}') )
    
    if action_schedule:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Выберите сотрудника.', reply_markup=rmk),
            fill_schedule,
            bot=bot
        )
    else:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Выберите сотрудника.', reply_markup=rmk),
            see_schedule,
            bot=bot
        )



def change_day_in_schedule(message: Message, bot: TeleBot):
    admin = bot.db.is_admin(employee_id=message.from_user.id)

    if not admin:
        bot.send_message(message.chat.id, '📛 <b>Отказано в доступе!</b>\nДанная команда доступна только администрации!')
        return

    select_department_to_change_schedule(message=message, bot=bot)


def select_department_to_change_schedule(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('FrontLine'), KeyboardButton('CallCentre'))
    rmk.add(KeyboardButton('ОТК'), KeyboardButton('Онлайн-заявления'))
    rmk.add(KeyboardButton('Администрация'), KeyboardButton('Ресепшн'))        
    rmk.add(KeyboardButton('Отмена'))
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберите отдел сотрудника.', reply_markup=rmk),
        select_employee_to_change_schedule,
        bot=bot
    )


def select_employee_to_change_schedule(message: Message, bot: TeleBot):
    department = message.text

    if department == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton(f'Изменить график сотрудника'))
        bot.send_message(message.chat.id, f'Процесс изменения графика остановлен.', reply_markup=rmk)
        
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    employees = bot.db.get_employees_via_department(employees_department=department)
    
    if not employees:
        bot.send_message(message.chat.id, '<b>Вы выбрали неправильный отдел!</b>')
        select_department_to_fill_and_see_schedule(bot=bot)
        return
    
    for i in employees:
        rmk.add(KeyboardButton(f'{i["fullname"]}') )
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберите сотрудника.', reply_markup=rmk),
        change_schedule_get_date,
        bot=bot
    )



def change_schedule_get_date(message: Message, bot: TeleBot):
    employee = bot.db.get_employee_data_via_fullname(employee_fullname=message.text)
    
    bot.send_message(message.chat.id, '🔸 Вы начали процесс заполнения графика за сотрудника.')
        
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Сегодня'), KeyboardButton('Завтра'))
    rmk.add(KeyboardButton('Отмена'))
    print(employee)

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите дату в формате DD.MM, или выберите из предложенных варинатов.\n<code>Например, 08.07.</code>', reply_markup=rmk),
        change_day_get_time,
        employee_id = employee['id'],
        bot=bot
    )



def change_day_get_time(message: Message, bot: TeleBot, employee_id):
    date_start_str = message.text

    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Изменить график сотрудника'))
        
        bot.send_message(message.chat.id, 'Процесс изменения графика остановлен.', reply_markup=rmk)
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('9:00 - 15:00'), KeyboardButton('10:00 - 16:00'))
    rmk.add(KeyboardButton('9:00 - 16:00'), KeyboardButton('10:00 - 17:00'))
    rmk.add(KeyboardButton('11:00 - 18:00'), KeyboardButton('9:00 - 18:00'))
    rmk.add(KeyboardButton('Отмена'))

    if date_start_str in ['Сегодня', 'Завтра']:
        date_start = utils.get_week_date(period=date_start_str)
    elif utils.check_date_format(date_start_str):
        date_start = datetime.strptime(date_start_str + ".2024", "%d.%m.%Y")
    else: 
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы неверно указали дату.\nВведите дату начала рабочей недели в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\nНапример, <code>Например, 08.07.</code>', reply_markup=rmk),
            change_day_get_time,
            employee_id = employee_id, bot=bot
        )
        return
    
    workday = bot.db.get_employee_schedule_information(employee_id = employee_id, workday = date_start)
    
    if workday is None:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))

        bot.send_message(message.chat.id, '<b>График сотрудника в этот день не заполнен!</b>\nПри ошибочном заполнении графика, а также при сбоях в работе обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
        return
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите время начала и окончания рабочего дня, в формате <b>10:00 - 20:00</b>.', reply_markup=rmk),
        change_shedule_send_info,
        date_start = date_start, employee_id = employee_id, bot=bot
    )


def change_shedule_send_info(message: Message, bot: TeleBot, date_start, employee_id):
    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Изменить график сотрудника'))

        bot.send_message(message.chat.id, 'Процесс изменения графика остановлен.', reply_markup=rmk)
        return
    
    worktimelist = utils.parse_time_range(message.text)
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Отмена'))
    
    if not worktimelist:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы неверно указали рабочее время.\nВведите время начала и окончания рабочего дня, в формате <b>10:00 - 20:00</b>.', reply_markup=rmk),
            change_shedule_send_info,
            date_start = date_start, employee_id = employee_id, bot=bot
        )
        return
    employee = bot.db.get_employee_data(employee_id=employee_id)
    
    result = bot.db.change_schedule(employee_id=employee_id, start_date=date_start, worktime=worktimelist)
    bot.send_message(message.chat.id, '<code>Информация загружается...</code>')
    # sleep(5)
    if result:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Изменить график сотрудника'))

        workday_new = bot.db.get_employee_schedule_information(employee_id=employee_id, workday=date_start)
        start_time_str = datetime.fromtimestamp(workday_new["start_datetime"]).strftime('%H:%M')
        end_time_str = datetime.fromtimestamp(workday_new["end_datetime"]).strftime('%H:%M')

        bot.send_message(message.chat.id, '<b>График сотрудника успешно изменен!</b>', reply_markup=rmk)
        
        admin_message_text = f'📆 Сотрудниу отдела {employee["department"]}, {employee["name"]} {employee["surname"]} изменили график.\n'
        admin_message_text += f'Дата: {date_start.strftime("%d.%m.%Y")}, время: {start_time_str} - {end_time_str}\n'
        admin_info = bot.db.get_employee_data(employee_id=message.from_user.id)
        admin_message_text += f'Команда была выполнена администратором {admin_info["name"]} {admin_info["surname"]}\n'
        admin_message_text += f'Связь с администратором: @{message.from_user.username}'
        bot.send_message(ADMIN_CHAT, admin_message_text)

        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Посмотреть график'))

        start_time_str = datetime.fromtimestamp(workday_new["start_datetime"]).strftime('%H:%M')
        end_time_str = datetime.fromtimestamp(workday_new["end_datetime"]).strftime('%H:%M')
        user_message = f'📍 <b>{date_start.strftime("%d.%m.%Y")}</b>: c {start_time_str} до {end_time_str}\n'
        
        bot.send_message(employee_id, f'❕ Администратор <b>{admin_info["name"]} {admin_info["surname"]}</b> изменил Вам график:\n{user_message}', reply_markup=rmk)

    else:
        schedule = bot.db.get_employee_schedule_via_startdate(employee_id=employee_id, startdate=date_start)
        start_time_str = datetime.fromtimestamp(schedule[0]["start_datetime"]).strftime('%H:%M')
        end_time_str = datetime.fromtimestamp(schedule[0]["end_datetime"]).strftime('%H:%M')

        bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 

        warn_message = f'При попытке изменить график сотруднику отдела {employee["department"]}, {employee["name"]} {employee["surname"]} произошла ошибка.'
        warn_message += f'Дата: {date_start.strftime("%d.%m.%Y")}, время: {start_time_str} - {end_time_str}\n'
        admin_info = bot.db.get_employee_data(employee_id=message.from_user.id)
        warn_message += f'\nКоманда была выполнена администратором {admin_info["name"]} {admin_info["surname"]}'
        warn_message += f'Связь с сотрудником, выполнившим команду: @{message.from_user.username}'
        bot.send_warn(warn_message)        
        




def see_filled_schedule(message: Message, bot: TeleBot):
    admin = bot.db.is_admin(employee_id=message.from_user.id)

    if not admin:
        bot.send_message(message.chat.id, '📛 <b>Отказано в доступе!</b>\nДанная команда доступна только администрации!')
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Текущая неделя'), KeyboardButton('Следующая неделя'))
    rmk.add(KeyboardButton('Отмена'))
    
    bot.send_message(message.chat.id, '🔸 Вы начали процесс просмотра заполненных графиков.')
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите дату, за которую хотите просмотреть заполненные графики, в формате DD.MM.\n<code>Например, 08.07.</code>', reply_markup=rmk),
        see_filled_schedule_get_workday,
        bot=bot
    )

def see_filled_schedule_get_workday(message: Message, bot: TeleBot):
    date_start_str = message.text
    if date_start_str == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Посмотреть заполненные графики'))
        bot.send_message(message.chat.id, 'Процесс просмотра заполненных графиков остановлен.', reply_markup=rmk)
        return
    if date_start_str in ['Текущая неделя', 'Следующая неделя']:
        date_start = utils.get_week_date(period=date_start_str)
    elif utils.check_date_format(date_start_str):
        date_start = datetime.strptime(date_start_str + ".2024", "%d.%m.%Y")
    else: 
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка!</b> Вы неверно указали дату.\nВведите дату начала рабочей недели в формате DD.MM.\nУчтите, что дата начала рабочей недели - понедельник.\nНапример, <code>Например, 08.07.</code>', reply_markup=rmk),
            see_filled_schedule_get_workday,
            bot=bot
        )
        return
    
    filled_schedules = bot.db.get_employees_schedule_via_date(workday=date_start.timestamp())
    not_filled_schedules = bot.db.get_employess_whose_schedule_not_filled(workday=date_start.timestamp())
    
    answer = '✅📆 Заполненные графики:\n\n'
    for i in filled_schedules:
        start_time_str = datetime.fromtimestamp(i["start_datetime"]).strftime('%H:%M')
        end_time_str = datetime.fromtimestamp(i["end_datetime"]).strftime('%H:%M')

        answer += f'📍 <b>{i["department"]}, {i["employee_fullname"]}</b>: c {start_time_str} до {end_time_str}\n'

    bot.send_message(message.chat.id, answer)

    answer = '❌📆 Графики не заполнены:\n\n'

    for i in not_filled_schedules:
        answer += f'📍 <b>{i["department"]}</b>: {i["employee_fullname"]}\n'

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Заполнить график сотрудника'))

    bot.send_message(message.chat.id, answer, reply_markup=rmk)
    

def admin_fill_and_seeschedule(message: Message, bot: TeleBot):
    admin = bot.db.is_admin(employee_id=message.from_user.id)
    head = bot.db.is_head(employee_id=message.from_user.id)

    if not (admin or head):
        bot.send_message(message.chat.id, '📛 <b>Отказано в доступе!</b>\nДанная команда доступна только администрации!')
        return

    action_schedule = True if message.text == 'Заполнить график сотрудника' else False
    bot.send_message(message.chat.id, f'🔸 Вы начали процесс {"заполнения" if action_schedule else "просмотра"} графика сотрудника.')
    select_department_to_fill_and_see_schedule(employee_id = message.from_user.id, employee_chat_id = message.chat.id, admin=admin, head=head, action_schedule=action_schedule, bot=bot)

def select_department_to_fill_and_see_schedule(employee_id, employee_chat_id, admin, head, action_schedule, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if admin:
        rmk.add(KeyboardButton('FrontLine'), KeyboardButton('CallCentre'))
        rmk.add(KeyboardButton('ОТК'), KeyboardButton('Онлайн-заявления'))
        rmk.add(KeyboardButton('Администрация'), KeyboardButton('Ресепшн'))
    elif head:
        employee = bot.db.get_employee_department(employee_id=employee_id)
        bot.send_message(employee_chat_id, f'Вам {"доступно заполнение" if action_schedule else "доступен просмотр"} графиков сотрудников только своего отдела.')
        rmk.add(KeyboardButton(f'{employee["department"]}'))
        
    rmk.add(KeyboardButton('Отмена'))
    
    bot.register_next_step_handler(
        bot.send_message(employee_chat_id, 'Выберите отдел сотрудника.', reply_markup=rmk),
        select_employee_to_fill_and_see_schedule,
        action_schedule = action_schedule,
        admin=admin, head=head,
        employee_id=employee_id, employee_chat_id=employee_chat_id,
        bot=bot
    )



def select_department_to_send_notify(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    admin = bot.db.is_admin(employee_id=message.from_user.id)
    if admin:
        rmk.add(KeyboardButton('FrontLine'), KeyboardButton('CallCentre'))
        rmk.add(KeyboardButton('ОТК'), KeyboardButton('Онлайн-заявления'))
        rmk.add(KeyboardButton('Администрация'), KeyboardButton('Ресепшн'))
        rmk.add(KeyboardButton('Все'))
        rmk.add('Отмена')

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберите отдел сотрудника.', reply_markup=rmk),
        select_employee_to_send_notify,
        bot=bot
    )

def select_employee_to_send_notify(message: Message, bot: TeleBot):
    department = message.text

    if department == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить оповещение'))
        bot.send_message(message.chat.id, f'Процесс отправки оповещения остановлен.', reply_markup=rmk)
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if department == 'Все':
        employees = bot.db.get_employees()

    
    employees = bot.db.get_employees_via_department(employees_department=department)
    
    if not employees:
        bot.send_message(message.chat.id, '<b>Вы выбрали неправильный отдел!</b>')
        
        return
    
    for i in employees:
        rmk.add(KeyboardButton(f'{i["fullname"]}') )
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберите сотрудника.', reply_markup=rmk),
        get_text_to_send_notify,
        bot=bot
    )

def get_text_to_send_notify(message: Message, bot: TeleBot):
    employee_name = message.text
    
    if employee_name == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить оповещение'))
        bot.send_message(message.chat.id, f'Процесс отправки оповещения остановлен.', reply_markup=rmk)
        return
    
    if employee_name == 'Все':
        employee = bot.db.get_employees()
        is_all = True
    else:
        employee = bot.db.get_employee_data_via_fullname(employee_name)
        is_all = False

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Отмена'))

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите текст оповещения.', reply_markup=rmk),
        send_notify,
        bot=bot, employee=employee, is_all=is_all
    )

def send_notify(message: Message, bot: TeleBot, employee, is_all):
    text = message.text
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить ответ'))

    if text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить оповещение'))

        bot.send_message(message.chat.id, 'Отправка ответа отменена.', reply_markup=rmk)
        return
    
    admin_info = bot.db.get_employee_data(message.from_user.id)

    if is_all:
        for i in employee:
            bot.send_message(i['id'], f'Администратор {admin_info["fullname"]} отправил Вам оповещение:\n{text}', reply_markup=rmk)
    else:  
        bot.send_message(employee['id'], f'Администратор {admin_info["fullname"]} отправил Вам оповещение:\n{text}', reply_markup=rmk)

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('/admin'), KeyboardButton('Отправить оповещение'))

    bot.send_message(message.chat.id, 'Ваше оповещение было успешно отправлено.', reply_markup=rmk)


def send_notify_answer(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Отмена'))
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите текст ответа.', reply_markup=rmk),
        send_notify_answer_text,
        bot=bot
    )

def send_notify_answer_text(message: Message, bot: TeleBot):
    text = message.text

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить ответ'))

    if text == 'Отмена':
        bot.send_message(message.chat.id, 'Отправка ответа отменена.')
        return
    
    employee = bot.db.get_employee_data(message.from_user.id)

    bot.send_message(chat_id=734902544, text=f'Вам пришел ответ от сотрудника {employee["fullname"]}:\n{text}')
    bot.send_message(message.chat.id, 'Ваш ответ успешно отправлен.')



    


# rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
# rmk.add(KeyboardButton('Сегодня'), KeyboardButton('Завтра'))
# rmk.add(KeyboardButton('Отмена'))

# bot.send_message(message.chat.id, '🔸 Вы начали процесс изменения графика в определенный день.')
# bot.register_next_step_handler(
#     bot.send_message(message.chat.id, 'Введите дату начала рабочей недели в формате DD.MM, или выберите из предложенных варинатов.\nУчтите, что дата начала рабочей недели - понедельник.\n<code>Например, 08.07.</code>', reply_markup=rmk),
#     fill_schedule_get_time,
#     bot=bot
# )