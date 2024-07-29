import asyncio

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ApplicationBuilder, Updater



CONTACT_DEVELOPER_TEXT = '\nОбратитесь к разработчку бота <a href="https://t.me/iplexa">Алексею Шипилову</a>'

async def send_account_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'{chr(0x26D4)} Вы не зарегистрированы!' + CONTACT_DEVELOPER_TEXT,
            parse_mode='HTML'
        )
    
