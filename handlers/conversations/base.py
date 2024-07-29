from typing import Any
from dataclasses import dataclass

from telegram import Update, Message, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler


class BaseConversation:
    # Константы, которые должны быть установлены в наследуемых классах
    CONV_NAME: str = None
    ENTRY_FUNCTION_NAME: str = None
    STATE_FUNCTIONS_NAMES: dict[int, str] = None

    # Общие константы
    PREV_STATE_CONV_CALLBACK_DATA = 'prev'
    END_CONV_CALLBACK_DATA = 'cancel'

    PREV_STATE_INLINE_BUTTON = InlineKeyboardButton(text='Назад', callback_data=PREV_STATE_CONV_CALLBACK_DATA)
    CANCEL_INLINE_BUTTON = InlineKeyboardButton(text='Отмена', callback_data=END_CONV_CALLBACK_DATA)

    MULTIPLICATION_SIGN = chr(0x00D7)

    @classmethod
    def get_conversation_handler(cls) -> ConversationHandler:
        raise NotImplementedError('This method is not implemented in the inherited class')

    @classmethod
    def start_conversation(cls) -> int:
        raise NotImplementedError('This method is not implemented in the inherited class')

    @classmethod
    async def go_previous_conv_state(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
        query = update.callback_query

        await query.answer()

        # Номер текузего состояния - это номер следующего состояния относительно текста прдыдущего
        current_state = context.user_data[cls.CONV_NAME].state

        if current_state-1 == 0:
            # Если номер предыдущего состояния равен 0, то есть самому первому состоянию,
            # то получаем и вызываем функцию начала диалога в принципе
            previous_state_function = cls.get_handler_by_name(
                name=cls.ENTRY_FUNCTION_NAME
            )
        else:
            # Получаем функцию придыдщего состояния
            previous_state_function = cls.get_handler_by_name(
                name=cls.STATE_FUNCTIONS_NAMES[current_state-2]
            )

        # Вызываем нужную функцию и возвращаем номер обработчика, который обработает следующий update от пользователя
        return await previous_state_function(update=update, context=context, from_prev_state=True)

    @classmethod
    async def end_conversation(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
        if update.callback_query.data == cls.END_CONV_CALLBACK_DATA:
            await update.callback_query.edit_message_text(
                text=f'{chr(0x1F6AB)} Действие отменено'
            )
            
            # Очищаем user_data от данных конкретного диалога, в котором была нажата кнопка "Отмена"
            context.user_data.pop(cls.CONV_NAME, None)

            await update.callback_query.answer()
        else:
            await update.callback_query.answer(text='Произошла неизвестная ошибка. Обратитесь к разработчику')

        return ConversationHandler.END


@dataclass
class ConversationData:
    conv_class: BaseConversation
    message: Message = None
    state: int = None
    data: Any = None
