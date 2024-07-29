from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
import xlsxwriter

from datetime import datetime, timedelta

import utils

from constants import GENERIC_CHAT, REPORT_THREAD_ID


def day_report_start(message: Message, bot: TeleBot):
    if not bot.db.is_emloyee_has_permission(message.from_user.id, ['Администрация']):
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'))
        
        bot.send_message(message.chat.id, '<b>Данная команда доступна только администрации!</b>', reply_markup=rmk)
        return
    
    bot.send_message(message.chat.id, '🔸 Вы начали процесс формирования отчета за день.')

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
    rmk.add(KeyboardButton('Отмена'))

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Необходимо ли рабочее время сотрудников?', reply_markup=rmk),
        day_report_get_date,
        bot=bot
    )

    


def day_report_get_date(message: Message, bot: TeleBot):
    ans = message.text

    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Сформировать отчет'))
        bot.send_message(message.chat.id, 'Процесс формирования отчета за день остановлен.', reply_markup=rmk)
        return
    
    if ans == 'Да':
        time_needed = True
    elif ans == 'Нет':
        time_needed = False
    else:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
        rmk.add(KeyboardButton('Отмена'))
        
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '<b>Ошибка! Вы выбрали неверный вариант ответа. Пожалуйста, выберите из доступных вариантов.</b>\nНеобходимо ли рабочее время сотрудников?', reply_markup=rmk),
            day_report_get_date,
            bot=bot
        )
        return
        

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Вчера'), KeyboardButton('Сегодня'))
    rmk.add(KeyboardButton('Отмена'))
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите дату, за которую требуется отчет в формате DD.MM.\n<code>Например, 08.07.</code>', reply_markup=rmk),
        day_report_select_department,
        time_needed=time_needed, bot=bot
    )

def day_report_select_department(message: Message, time_needed: bool, bot: TeleBot):
    time_needed = time_needed
    date_str = message.text

    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Сформировать отчет'))
        bot.send_message(message.chat.id, 'Процесс  формирования отчета за день остановлен.', reply_markup=rmk)
        return
    
    if date_str in ['Вчера', 'Сегодня', 'Завтра']:
        date = utils.get_week_date(date_str)
    elif utils.check_date_format(date_str):
        date = datetime.strptime(date_str + ".2024", "%d.%m.%Y")
    else:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Вчера'), KeyboardButton('Сегодня'))
        rmk.add(KeyboardButton('Отмена'))
        
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите дату, за которую требуется отчет в формате DD.MM.\n<code>Например, 08.07.</code>', reply_markup=rmk),
            day_report,
            time_needed=time_needed, bot=bot
        )
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Онлайн-заявления'), KeyboardButton('FrontLine'))
    rmk.add(KeyboardButton('ОТК'), KeyboardButton('CallCentre'))
    rmk.add(KeyboardButton('Полный отчет'))
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберите отдел.', reply_markup=rmk),
        day_report,
        date = date, time_needed=time_needed, bot=bot
    )

def day_report(message: Message, bot: TeleBot, date: datetime, time_needed: bool, is_auto: bool = False):
    if is_auto:
        departments = ['Онлайн-заявления', 'FrontLine', 'ОТК', 'CallCentre']
    
    else:
        ans = message.text

        if ans == 'Полный отчет':
            departments = ['Онлайн-заявления', 'FrontLine', 'ОТК', 'CallCentre']
        else:
            departments = [ans]
    
    for j in departments:
        is_otk = True if j == 'ОТК' else False
        is_callcentre = True if j == 'CallCentre' else False
        
        if is_callcentre:
            employees = bot.db.get_employees_have_bitrix()
        else:
            employees = bot.db.get_employees_via_department(employees_department=f'{j}')
        
        answer = f'<b>Отдел {j}:</b>\n'
        
        total_count = 0

        for employee in employees:
            answer += f'\nСотрудник {employee["fullname"]}:\n'
            date_int = date.timestamp()
            if time_needed:
                workday_info = bot.db.get_employee_workday_information(employee["id"], workday=date_int)
                workday_none, workday_end_time = False, False
                
                if workday_info is None:
                    answer += f' 📍 Сотрудник не работал в этот день.\n'
                    workday_none = True
                
                if not workday_none:
                    start_time_str = workday_info["start_time"].strftime("%H:%M") 

                    if workday_info["end_time"] is None:
                        answer += f' 📍 Сотрудник начал работать с {start_time_str} и не завершил рабочий день.\n'
                        workday_end_time = True
                    
                    if not workday_end_time:
                        time_worked = workday_info["end_time"].timestamp() - workday_info["start_time"].timestamp()
                        
                        time_worked_str = utils.seconds_to_simple_time_str(seconds=time_worked)

                        end_time_str = workday_info["end_time"].strftime("%H:%M")

                        employee_schedule = bot.db.get_employee_schedule_information(
                            employee_id=employee["id"], 
                            workday=date
                        )

                        if employee_schedule:
                            overwork = time_worked - (employee_schedule['end_datetime'] - employee_schedule['start_datetime'])
                            if overwork < 0:
                                overwork_str = '-' + utils.seconds_to_simple_time_str(seconds=abs(overwork))
                            else:
                                overwork_str = utils.seconds_to_simple_time_str(seconds=overwork)
                        
                        else:
                            overwork_str = 'График сотрудника не заполнен.'
                        
                        answer += f' 📍 Отработал {time_worked_str} с {start_time_str} по {end_time_str}.\n'
                        answer += f' 📍 Переработка: {overwork_str}\n'

            if is_callcentre:
                count_calls = bot.db.get_daytime_calls_via_employee_id(employee_id=employee["id"], date=date) 
                answer += f' 📍 Ответил на {count_calls["calls_count"]} звонков.\n'
                continue

            count_otk = bot.db.get_daytime_applications_via_employee_id(employee_id=employee["id"], date=date, is_otk=True)
            count = bot.db.get_daytime_applications_via_employee_id(employee_id=employee["id"], date=date, is_otk=False)

            if is_otk:
                answer += f' 📍 Проверил {count_otk["applications_count"]} личных дел.\n'

                if count["applications_count"] > 0:
                    answer += f'   📍 Также обработал {count["applications_count"]} заявлений.\n'

            else:            
                answer += f' 📍 Обработал {count["applications_count"]} заявлений.\n'

                if count_otk["applications_count"] > 0:
                    answer += f'   📍 Также проверил {count_otk["applications_count"]} личных дел.\n'

                    continue
        
        if j == 'CallCentre':
            total_count = bot.db.get_daytime_work_count(date=date, department=j)['calls_count']
        else:
            total_count = bot.db.get_daytime_work_count(date=date, department=j)['applications_count']

        if is_otk:
            answer += f'\n<b>Итого проверено: </b><u>{total_count}</u>'
        elif is_callcentre:
            answer += f'\n<b>Итого звонков: </b><u>{total_count}</u>'
        else:
            answer += f'\n<b>Итого заявлений: </b><u>{total_count}</u>'
        
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Сформировать отчет'))
        
        if is_auto:
            bot.send_message(chat_id=GENERIC_CHAT, message_thread_id=REPORT_THREAD_ID, text=answer)     
        else:
            bot.send_message(message.chat.id, answer, reply_markup=rmk)     




def day_report_xlsx(message: Message, bot: TeleBot):
    start_message = bot.send_message(message.chat.id, 'Формирование отчета началось и может занять до двух минут.')
    start_date = datetime.strptime("25.06.2024", "%d.%m.%Y")

    today = datetime.today()
    num_days = (today - start_date).days + 1

    workbook = xlsxwriter.Workbook('report.xlsx')
    worksheet = workbook.add_worksheet()

    header_format = workbook.add_format({'bold': True, 'align': 'center'})
    date_format = workbook.add_format({'align': 'center'})
    cell_format = workbook.add_format({'align': 'center'})

        # Merge the cells in the first row
    for i in range(num_days):
        merge_range = xlsxwriter.utility.xl_range(0, 1 + i * 3, 0, 3 + i * 3 - 1)
        date = (start_date + timedelta(days=i)).strftime('%d.%m.%Y')
        worksheet.merge_range(merge_range, date, date_format)

    # Set the column headers
    headers = ['Время работы', 'Переработка', 'Количество выполненной работы']
    for i in range(num_days):
        for j, header in enumerate(headers):
            worksheet.write(1, 1 + i * 3 + j, header, header_format)

    worksheet.set_column(0, 0, 20)  # fullname column
    worksheet.set_column(1, num_days * 3, 15)  # other columns

    worksheet.set_row(0, 25)  # header row
    worksheet.set_row(1, 20)  # data rows


    departments = ['Онлайн-заявления', 'FrontLine', 'ОТК', 'CallCentre']
    
    row_index = 1
    for j in departments:
        is_otk = True if j == 'ОТК' else False
        is_callcentre = True if j == 'CallCentre' else False

        worksheet.write_row(row_index, 0, [j])
        row_index += 1

        if is_callcentre:
            employees = bot.db.get_employees_have_bitrix()
        else:
            employees = bot.db.get_employees_via_department(employees_department=f'{j}')

        for employee in employees:
            row = [employee["fullname"]]
            for i in range(num_days):
                date = start_date + timedelta(days=i)
                date_int = date.timestamp()
                workday_info = bot.db.get_employee_workday_information(employee["id"], workday=date_int)
                workday_none, workday_end_time = False, False


                if workday_info is None:
                    time_worked_str, overwork_str, count_str = '', '', ''
                else:
                    start_time_str = datetime.fromtimestamp(workday_info["start_time"]).strftime("%H:%M")
                    if workday_info["end_time"] is None:
                        time_worked_str, overwork_str, count_str = '', '', ''
                    else:
                        time_worked = workday_info["end_time"] - workday_info["start_time"]
                        time_worked_str = utils.seconds_to_simple_time_str(seconds=time_worked)
                        end_time_str = datetime.fromtimestamp(workday_info["end_time"]).strftime("%H:%M")

                        employee_schedule = bot.db.get_employee_schedule_information(
                            employee_id=employee["id"],
                            workday=date
                        )

                        if employee_schedule:
                            overwork = time_worked - (employee_schedule['end_datetime'] - employee_schedule['start_datetime'])
                            if overwork < 0:
                                overwork_str = '-' + utils.seconds_to_simple_time_str(seconds=abs(overwork))
                            else:
                                overwork_str = utils.seconds_to_simple_time_str(seconds=overwork)
                        else:
                            overwork_str = 'График сотрудника не заполнен.'

                if is_callcentre:
                    count_calls = bot.db.get_daytime_calls_via_employee_id(employee_id=employee["id"], date=date)
                    count_str = f'{count_calls["calls_count"]} звонков'
                else:
                    count_otk = bot.db.get_daytime_applications_via_employee_id(employee_id=employee["id"], date=date, is_otk=True)
                    count = bot.db.get_daytime_applications_via_employee_id(employee_id=employee["id"], date=date, is_otk=False)

                    if is_otk:
                        count_str = f'{count_otk["applications_count"]} личных дел'
                    else:
                        count_str = f'{count["applications_count"]} заявлений'

                row.extend([time_worked_str, overwork_str, count_str])

               
            bot.edit_message_text(message_id=start_message.id, text=f'Выгрузка данных сотрудника {employee["fullname"]}...', chat_id=message.chat.id)

            worksheet.write_row(row_index, 0, row)
            row_index += 1

    workbook.close()

    bot.edit_message_text(message_id=start_message.id, text=f'Формирование отчета завершено. Файл отправляется...', chat_id=message.chat.id)
    bot.send_document(message.chat.id, document=open('report.xlsx', 'rb'))