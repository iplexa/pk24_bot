from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

import time
import schedule

from datetime import datetime

from .reports import day_report
from utils import get_week_date

from constants import GENERIC_CHAT, REPORT_THREAD_ID

employee_data = None


def update_employee_data(bot: TeleBot):
    global employee_data
    
    while True:
        employee_data = bot.db.get_employees_schedule_via_date(workday=get_week_date("Сегодня").timestamp())
        # print('employee_data There is a data' if employee_data else 'employee_data There isnt data')
        time.sleep(600)


def check_reminders(bot: TeleBot):
    global employee_data
    
    while True:
        time.sleep(1)
        
        current_time = datetime.now().timestamp()

        if employee_data is not None:
            for employee in employee_data:
                start_diff = abs(current_time - employee['start_datetime'])
                end_diff = abs(current_time - employee['end_datetime'])
                # print(f"employee {employee['employee_id']} / fullname {employee['employee_fullname']} / start {datetime.fromtimestamp(employee['start_datetime']).strftime('%H:%M')} / end {datetime.fromtimestamp(employee['end_datetime']).strftime('%H:%M')} / start_diff {start_diff} / end_diff {end_diff}\n\n")
                
                workday=get_week_date("Сегодня").timestamp()
                workday_info = bot.db.get_employee_workday_information(employee["employee_id"], workday=workday)
                
                if start_diff <= 40 and workday_info is None:
                    bot.send_message(employee['employee_id'], '<b>Вам пора начать рабочий день!</b>')
                elif end_diff <= 40 and (workday_info is not None and workday_info['end_time'] is None):
                    bot.send_message(employee['employee_id'], "<b>Вам пора закончить рабочий день!</b>")

        time.sleep(60)


def start_schedule(bot):
    schedule.every().day.at("19:00").do(day_report, bot=bot, date=get_week_date('Сегодня'), time_needed=True, is_auto=True, message=None)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
# def day_report(date: datetime, time_needed: bool, bot: TeleBot, is_auto: bool = False, message: Message = None):

# def day_report(message: Message, date: datetime, time_needed: bool, bot: TeleBot, is_auto: bool = False):
