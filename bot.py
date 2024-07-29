import logging
import inspect
import asyncio
from sys import stdout
from functools import partial
from os import system

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ApplicationBuilder, Updater
from datetime import datetime

from utils import Utils

from database import Database

from constants import TELEGRAM_BOT_TOKEN, ADMIN_CHAT, INFO_THREAD_ID, WARN_THREAD_ID, ERROR_THREAD_ID



logging.basicConfig(
    # filename='log.log',
    # filemode='a',
    # encoding='utf-8',
    stream=stdout,
    datefmt='%d.%m.%Y %H:%M:%S',
    format='[%(asctime)s] [%(levelname)s] [Thread: %(threadName)s] | %(message)s',
    level=logging.WARNING
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""

    user = update.effective_user

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=str(await context.application.db.get_employee(id=5163143779)),
        parse_mode='HTML'
    )

async def send_warn(context: ContextTypes.DEFAULT_TYPE, text: str = 'Unknown warn') -> None:
    text_log = text.replace('\n', ' ')
    called_from = inspect.stack()[1][0].f_code.co_name
    logging.warning(f'{text_log} / Called from: {called_from}')
    await context.bot.send_message(
        chat_id=ADMIN_CHAT, 
        message_thread_id=WARN_THREAD_ID,
        text=f'<code>{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</code>\n<b>WARN</b>\n{text}\nCalled from: {called_from}',
        parse_mode='HTML'
    )

async def send_error(application: Application, error, sql: str, data: dict, caller_function_name: str) -> None:
    logging.error(f'DATABASE ERROR: SQL: {sql} / DATA: {data} / Called from: {caller_function_name}')
    await application.bot.send_message(
        chat_id=ADMIN_CHAT,
        message_thread_id=ERROR_THREAD_ID,
        text=(
            f'<code>[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]</code>'
            f'\n<b>ERROR</b>\nError text: {error}\nSQL: {sql}\nDATA: {data}\nCalled from: {caller_function_name}'
            ),
        parse_mode='HTML'
    )

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.effective_message.text.split()

    if len(data) == 1:
        seconds = 1
    else:
        seconds = int(data[-1])
    
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Бот будет перезапущнен через {seconds} секунд.'
        )
    admin_message = await context.bot.send_message(
        chat_id=ADMIN_CHAT,
        message_thread_id=INFO_THREAD_ID,
        text=f'Бот будет перезапущнен через {seconds} секунд.\nКоманда была вызвана @{update.effective_user.username}'
    )
    await asyncio.sleep(seconds)
    
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message.message_id,
        text='Бот перезапускается...'
        )
    await context.bot.edit_message_text(
        chat_id=ADMIN_CHAT,
        message_id=admin_message.message_id,
        text=f'Бот перезапускается...\nКоманда была вызвана @{update.effective_user.username}'
        )
       
    quit(system('python "C:\\Users\\iplexa\\YandexDisk\\pk24\\dev\\bot.py"'))
 

async def post_init_bot(application):
    # Логинимся в базу
    await application.db.login()

    await application.bot.send_message(
        chat_id=ADMIN_CHAT,
        message_thread_id=INFO_THREAD_ID,
        text=f'<code>[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]</code>\nБот и все его компоненты успешно запущены.',
        parse_mode='HTML'
    )


async def post_shutdown_bot(application):
    caller_function_name=inspect.stack()[1][0].f_code.co_name

    await application.bot.send_message(
        chat_id=ADMIN_CHAT,
        message_thread_id=INFO_THREAD_ID,
        text=f'<code>[{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}]</code>\nBot is shutting down from <code>{caller_function_name}</code>...',
        parse_mode='HTML'
    )


def start_bot() -> None:
    """Start the bot."""
    from functools import partial as ft_partial
    from handlers.conversations.send_application import SendApplicationConversation

    from handlers.employee_workday import start_work, end_work

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.post_init = post_init_bot
    application.post_stop = post_shutdown_bot
    
    application.db = Database(on_error_callback=lambda error, sql, data, caller_function_name: send_error(application=application, error=error, sql=sql, data=data, caller_function_name=caller_function_name))
    application.send_warn = send_warn
    application.utils = Utils
    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler('start', start))
    application.add_handler(SendApplicationConversation.get_conversation_handler())
    application.add_handler(CommandHandler('restart', restart_bot))

    application.add_handler(CommandHandler('start_work', start_work))
    application.add_handler(CommandHandler('end_work', end_work))


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    start_bot()
