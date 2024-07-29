from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler


FULL_NAME, SNILS = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
        ]
    )

    if context.user_data.get('start_message_id', None) is None:
        start_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Вы начали процесс проверки работоспособности\nВведите ФИО абитуриента',
            reply_markup=reply_markup,
        )

        context.user_data['start_message_id'] = start_message.id
    else:
        await context.bot.edit_message_text(
            text='Введите ФИО абитуриента',
            chat_id=update.effective_chat.id,
            message_id=context.user_data['start_message_id'],
            reply_markup=reply_markup,
        )

    context.user_data['state'] = FULL_NAME

    return FULL_NAME


async def full_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['full_name'] = update.effective_message.text
    await update.effective_message.delete()

    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text='Назад', callback_data='prev')],
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')]
        ]
    )

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['start_message_id'],
        text=f'<i>Абитуриент:</i>\n{context.user_data["full_name"]}\nВведите номер СНИЛС',
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    context.user_data['state'] = SNILS

    return SNILS


async def snils_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['snils'] = update.effective_message.text
    await update.effective_message.delete()

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['start_message_id'],
        text=f'<i>Абитуриент:</i>\n{context.user_data["full_name"]}\n<i>СНИЛС:</i>\n{context.user_data["snils"]}\nПроцесс завершён',
        parse_mode='HTML'
    )

    context.user_data.clear()

    return -1





test_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters=filters.Regex('^Проверить работу$'), callback=start),
    ], 
    states={
        FULL_NAME: [
            MessageHandler(filters=filters.TEXT, callback=full_name_step),
        ],
        SNILS: [
            MessageHandler(filters=filters.TEXT, callback=snils_step),
            CallbackQueryHandler(callback=previous, pattern=f'^prev$')
        ]
    },
    fallbacks=[
        CallbackQueryHandler(callback=cancel, pattern=f'^cancel$')
    ],
)
