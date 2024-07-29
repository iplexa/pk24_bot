import logging
import inspect
import logging.config
import threading
import functools as ft

from time import sleep
from datetime import datetime
from telebot import TeleBot

from constants import ADMIN_CHAT, TELEGRAM_BOT_TOKEN
from db import Database


logging.basicConfig(
    filename='log.log',
    filemode='a',
    encoding='utf-8',
    datefmt='%d.%m.%Y %H:%M:%S',
    format='[%(asctime)s] [%(levelname)s] [Thread: %(threadName)s] | %(message)s',
    level=logging.INFO
)


def send_error(error, sql, data, call, bot: TeleBot):
    logging.error(f'DATABASE ERROR: SQL: {sql} / DATA: {data} / Called from: {call}')
    bot.send_message(ADMIN_CHAT, f'<code>{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</code>\n<b>DATABASE ERROR</b>\nsql = {sql}\ndata = {data}\n{error}, Called from: {call}')


def send_warn(text:str, bot: TeleBot):
    text_log = text.replace('\n', ' ')
    called_from = inspect.stack()[1][0].f_code.co_name
    logging.warning(f'{text_log} / Called from: {called_from}')
    bot.send_message(ADMIN_CHAT, f'<code>{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</code>\n<b>WARN</b>\n{text}\nCalled from: {called_from}')


def initialize_bot(database_path: str) -> None:
    from handlers.generic import response_to_start, register_get_department, information
    from handlers.admin import admin_menu, admin_fill_and_seeschedule, change_day_in_schedule, see_filled_schedule, select_department_to_send_notify, send_notify_answer
    from handlers.applications import find_applicant_start, send_application, select_applicaton_to_update_certificate_status, select_file_to_check
    from handlers.schedule import start_workday, end_workday, fill_schedule, see_schedule, heart
    from handlers.reports import day_report_start, day_report_xlsx 
    from handlers.reminder import update_employee_data, check_reminders, start_schedule

    from bitrix24 import Bitrix24API


    bot = TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='HTML', num_threads=3)
    bot.send_warn = ft.partial(send_warn, bot=bot)
    bot.send_error = ft.partial(send_error, bot=bot)
    bot.db = Database(db_file_path=database_path, on_error_callback=bot.send_error)
    bot.bitrix24 = Bitrix24API(bot=bot)
    
    # Регистрируем обработчики
    bot.register_message_handler(ft.partial(response_to_start, bot=bot), commands=['start'])
    bot.register_message_handler(ft.partial(register_get_department, bot=bot), commands=['register'])
    bot.register_message_handler(ft.partial(information, bot=bot), commands=['info'])
    bot.register_message_handler(ft.partial(information, bot=bot), func=lambda message: message.text == 'Список команд')

    bot.register_message_handler(ft.partial(admin_menu, bot=bot), commands=['admin'])
    bot.register_message_handler(ft.partial(admin_fill_and_seeschedule, bot=bot), func=lambda message: message.text in ['Заполнить график сотрудника', 'Посмотреть график сотрудника'])
    bot.register_message_handler(ft.partial(change_day_in_schedule, bot=bot), func=lambda message: message.text in ['Изменить график сотрудника'])
    bot.register_message_handler(ft.partial(see_filled_schedule, bot=bot), func=lambda message: message.text in ['Посмотреть заполненные графики'])
    bot.register_message_handler(ft.partial(select_department_to_send_notify, bot=bot), func=lambda message: message.text in ['Отправить оповещение'])
    bot.register_message_handler(ft.partial(send_notify_answer, bot=bot), func=lambda message: message.text in ['Отправить ответ'])



    bot.register_message_handler(ft.partial(find_applicant_start, bot=bot), func=lambda message: message.text == 'Найти заявление')
    bot.register_message_handler(ft.partial(send_application, bot=bot), func=lambda message: message.text == 'Отправить заявление')
    bot.register_message_handler(ft.partial(select_applicaton_to_update_certificate_status, bot=bot), func=lambda message: message.text == 'Внести аттестат')
    bot.register_message_handler(ft.partial(select_file_to_check, bot=bot), func=lambda message: message.text == 'Проверить дело')

    bot.register_message_handler(ft.partial(start_workday, bot=bot), func=lambda message: message.text == 'Начать рабочий день')
    bot.register_message_handler(ft.partial(end_workday, bot=bot), func=lambda message: message.text == 'Завершить рабочий день')
    bot.register_message_handler(ft.partial(fill_schedule, bot=bot), func=lambda message: message.text == 'Заполнить график')
    bot.register_message_handler(ft.partial(see_schedule, bot=bot), func=lambda message: message.text == 'Посмотреть график')
    bot.register_message_handler(ft.partial(heart, bot=bot), func=lambda message: message.text == 'heart')

    
    bot.register_message_handler(ft.partial(day_report_start, bot=bot), func=lambda message: message.text == 'Сформировать отчет')
    bot.register_message_handler(ft.partial(day_report_xlsx, bot=bot), func=lambda message: message.text == 'Сформировать excel')

    # Запускаем бота
    # bot.infinity_polling(skip_pending=True, logger_level=20, timeout=5)
    threading.Thread(
        target=bot.infinity_polling,
        kwargs={'skip_pending': True, 'logger_level': 20, 'timeout': 5},
        name='TeleBot',
        daemon=True
    ).start()

    threading.Thread(
        target=update_employee_data,
        kwargs={'bot': bot},
        name='reminder_update_employee_data',
        daemon=True
    ).start()

    threading.Thread(
        target=check_reminders,
        kwargs={'bot': bot},
        name='reminder_employee_schedule',
        daemon=True
    ).start()

    threading.Thread(
        target=start_schedule,
        kwargs={'bot': bot},
        name='start_schedule',
        daemon=True
    ).start()

    # Запускаем Битрикс24
    # bot.bitrix24.start_listen_outgoing_webhooks(host='192.168.1.62', port=5050)
    threading.Thread(
        target=bot.bitrix24.start_listen_outgoing_webhooks,
        kwargs={'host': '192.168.1.62', 'port': 5050},
        name='Bitrix24API',
        daemon=True
    ).start()

    logging.info('Бот и все его компоненты успешно запущены')

    while True:
        try:
            sleep(1)
        except KeyboardInterrupt:
            bot.db.close()
            logging.info('Работа бота была завершена')
            exit()



if __name__ == '__main__':
    initialize_bot(database_path='database.db')
