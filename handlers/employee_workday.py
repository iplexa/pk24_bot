import asyncio

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from datetime import datetime, timedelta

import user_warns

from .conversations.base import BaseConversation, ConversationData
from database.models import Employee, EmployeesWorktime, EmployeeSchedule

from inline_buttons import COMMAND_LIST_INLINE_BUTTON
from constants import GENERIC_CHAT, TIME_THREAD_ID 
from database import Database



async def start_work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    employee: Employee = await context.application.db.get_employee(id=update.effective_user.id)

    if employee is None:
        user_warns.send_account_warn(update=update, context=context)
        return
    
    start_work_time_str = update.message.date.strftime('%d.%m.%Y %H:%M:%S')

    data = EmployeesWorktime(employee_id=update.effective_user.id, start_time=update.message.date)
    
    result = await context.application.db.insert_employee_start_work_info(data)

    if result:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'<b>Успешное начало рабочего дня!</b>\nЖелаем хорошей работы :)',
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[COMMAND_LIST_INLINE_BUTTON]])
        )
        await context.bot.send_message(
            chat_id=GENERIC_CHAT,
            message_thread_id=TIME_THREAD_ID,
            text=f'<code>[{start_work_time_str}]</code>\n{chr(0x25B6)*3}\nСотрудник приемной комиссии <b>{employee.first_name} {employee.last_name}</b> из отдела <b>{employee.department}</b> начал рабочий день.',
            parse_mode='HTML'
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'<b>Вы уже начали рабочий день!</b> При ошибочном начале рабочего дня:'+user_warns.CONTACT_DEVELOPER_TEXT,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[COMMAND_LIST_INLINE_BUTTON]])
        )
        await context.application.send_warn(context = context, text = f'Сотрудник <b>{employee.first_name} {employee.last_name}</b> из отдела <b>{employee.department}</b> попытался второй раз начать рабочий день!\nОбратиться: @{update.effective_user.username}')


async def end_work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    employee: Employee = await context.application.db.get_employee(id=update.effective_user.id)

    if employee is None:
        user_warns.send_account_warn(update=update, context=context)
        return
    
    end_work_time_str = update.message.date.strftime('%d.%m.%Y %H:%M:%S')

    data = EmployeesWorktime(employee_id=update.effective_user.id, end_time=update.message.date)
    
    try:
        result, data.start_time = await context.application.db.insert_employee_end_work_info(data)
    except Exception as e:
        # print(f'!!! ошибка[{e}]')
        message = '<b>Произошла ошибка!</b>\n'
        
        match str(e):
            case 'WorkdayAlreadyEnded':
                message += '<b>Вы уже завершили рабочий день!</b>'
            case 'WorkdayNotStarted':
                message += '<b>Вы не начали рабочий день!</b>'
            case _:
                message += '<i>Причина ошибки неизвестна.</i>'
        
        message += '\n\nПри ошибках в работе бота:' + user_warns.CONTACT_DEVELOPER_TEXT
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[COMMAND_LIST_INLINE_BUTTON]])
        )
        await context.application.send_warn(context = context, text = f'Сотрудник <b>{employee.employee_full_name()}</b> при завершении рабочего дня столкнулся с ошибкой <code>{str(e)}</code>. Обратиться: {update.effective_user.username}')
        
        result = False

    if result:
        time_worked = data.end_time - data.start_time
        # print('time_worked', time_worked)
        time_worked_str = context.application.utils.timedelta_to_str(time_worked)
        
        start_time_str = data.start_time.strftime('%H:%M')
        end_time_str = data.end_time.strftime('%H:%M')

        employee_schedule: EmployeeSchedule = await context.application.db.get_employee_schedule(employee_id=update.effective_user.id, today=True)

        if employee_schedule:
            overwork = time_worked - (employee_schedule.end_datetime - employee_schedule.start_datetime)
            overwork.seconds = 0
            
            if overwork < 0:
                overwork_str = context.application.utils.timedelta_to_simple_time_str(delta=abs(overwork))
            else:
                overwork_str = context.application.utils.timedelta_to_simple_time_str(delta=overwork)

                if overwork > timedelta(hours=2):
                    await context.application.send_warn(context=context, text=f'У Сотрудниа {employee.full_name} слишком большая переработка!\nПереработка: {overwork_str}\nСвязь с сотрудником: @{update.effective_user.username}')
        else:
            overwork_str = 'График сотрудника не заполнен.'
        
        message_str = (
            f'<code>[{end_work_time_str}]</code>\n⏸️⏸️⏸️\nСотрудник приемной комиссии <b>{employee.full_name}</b> из отдела <b>{employee.department}</b> закончил рабочий день.\n'
            f'Отработал {time_worked_str} с {start_time_str} по {end_time_str}.\n'
            f'Переработка: {overwork_str}'
        ) 

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='<b>Успешное завершение рабочего дня!</b>\nХорошего Вам отдыха!',
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[COMMAND_LIST_INLINE_BUTTON]])
        )

        await context.bot.send_message(
            chat_id=GENERIC_CHAT,
            message_thread_id=TIME_THREAD_ID,
            text=message_str,
            parse_mode='HTML'
        )






    