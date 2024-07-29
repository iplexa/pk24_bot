import re
import asyncio

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler

from database.models import Person, Application
from .base import BaseConversation, ConversationData


class SendApplicationConversation(BaseConversation):
    # Константы
    CONV_NAME = 'send_application'
    CONFIRM_INLINE_BUTTON = InlineKeyboardButton(text='Подтвердить', callback_data=CONV_NAME+'_confirm')

    # Состояния диалога
    ENTRY_FUNCTION_NAME = 'start_conversation'

    FULL_NAME, SPO_NUMBER, SUBMIT_METHOD, ORIGINAL_CERTIFICATE, CONFIRM = range(5)

    STATE_FUNCTIONS_NAMES = {
        FULL_NAME: 'full_name_handler',
        SPO_NUMBER: 'spo_number_handler',
        SUBMIT_METHOD: 'submit_method_handler',
        ORIGINAL_CERTIFICATE: 'original_certificate_handler',
        CONFIRM: 'confirm_handler'
    }

    @classmethod
    def get_conversation_handler(cls) -> ConversationHandler:
        conversation_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters=filters.Regex(pattern='^Отправить заявление$'), callback=cls.get_handler_by_name(cls.ENTRY_FUNCTION_NAME)),
                CommandHandler(command='sendapplication', callback=cls.start_conversation)
            ],
            states={
                cls.FULL_NAME: [
                    MessageHandler(filters=filters.TEXT, callback=cls.get_handler_by_name(cls.STATE_FUNCTIONS_NAMES[cls.FULL_NAME])),
                    CallbackQueryHandler(
                        callback=cls.go_previous_conv_state,
                        pattern=f'^{cls.PREV_STATE_CONV_CALLBACK_DATA}$'
                    )
                ],
                cls.SPO_NUMBER: [
                    MessageHandler(filters=filters.TEXT, callback=cls.get_handler_by_name(cls.STATE_FUNCTIONS_NAMES[cls.SPO_NUMBER])),
                    CallbackQueryHandler(
                        callback=cls.go_previous_conv_state,
                        pattern=f'^{cls.PREV_STATE_CONV_CALLBACK_DATA}$'
                    )
                ],
                cls.SUBMIT_METHOD: [
                    CallbackQueryHandler(
                        callback=cls.get_handler_by_name(cls.STATE_FUNCTIONS_NAMES[cls.SUBMIT_METHOD]),
                        pattern=f'^{cls.CONV_NAME}_submit_method*'
                    ),
                    CallbackQueryHandler(
                        callback=cls.go_previous_conv_state,
                        pattern=f'^{cls.PREV_STATE_CONV_CALLBACK_DATA}$'
                    )
                ],
                cls.ORIGINAL_CERTIFICATE: [
                    CallbackQueryHandler(
                        callback=cls.get_handler_by_name(cls.STATE_FUNCTIONS_NAMES[cls.ORIGINAL_CERTIFICATE]),
                        pattern=f'^{cls.CONV_NAME}_original_certificate*'
                    ),
                    CallbackQueryHandler(
                        callback=cls.go_previous_conv_state,
                        pattern=f'^{cls.PREV_STATE_CONV_CALLBACK_DATA}$'
                    )
                ],
                cls.CONFIRM: [
                    CallbackQueryHandler(
                        callback=cls.get_handler_by_name(cls.STATE_FUNCTIONS_NAMES[cls.CONFIRM]),
                        pattern=f'^{cls.CONV_NAME}_confirm$'
                    ),
                    CallbackQueryHandler(
                        callback=cls.go_previous_conv_state,
                        pattern=f'^{cls.PREV_STATE_CONV_CALLBACK_DATA}$'
                    )
                ]
            },
            fallbacks=[CallbackQueryHandler(callback=cls.end_conversation, pattern=f'^{cls.END_CONV_CALLBACK_DATA}$')]
        )

        return conversation_handler 

    @classmethod
    async def start_conversation(cls, update: Update, context: ContextTypes.DEFAULT_TYPE, error_text: str = None, from_prev_state: bool = False) -> int:
        bot = context.bot
        user_data = context.user_data

        # Если в функцию передан текст ошибки пользователя,
        # это значит, что диалог уже был ранее начат
        if error_text is not None:
            from_prev_state = True

        # Инициализируем словарь текущего разговора для его дальшейшего использования
        # Инициализация словаря происходит в случае, если в Update пришло сообщение от пользователя
        # о начале диалога; при условии нажатия кнопки "Назад" используется словарь,
        # который был сформирован в процессе диалога
        if not from_prev_state:
            user_data[cls.CONV_NAME] = ConversationData(conv_class=cls)

        # Текст начала диалога
        message_text = cls._get_message_text(
            user_data=user_data,
            state_text='Введите фамилию, имя и отчество (при наличии) абитуриента',
            error_text=error_text
        )

        if user_data[cls.CONV_NAME].message is None:
            # Сюда попадаем в случае начала нового диалога

            # СПРАВКА: при отправке или изменении сообщения бот возвращает объект Message
            conv_message = await bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[cls.CANCEL_INLINE_BUTTON]])
            )

            # Записываем объект Message в user_data, чтобы потом менять текст сообщения
            user_data[cls.CONV_NAME].message = conv_message
            
            # Инициализируем объект Application для его дальшейго заполнения и использования
            user_data[cls.CONV_NAME].data = Application(applicant=Person())
        else:
            # Сюда попадаем в случае нажатия кнопки "Назад"

            edited_conv_message = await bot.edit_message_text(
                text=message_text,
                chat_id=update.effective_chat.id,
                message_id=user_data[cls.CONV_NAME].message.id,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[cls.CANCEL_INLINE_BUTTON]])
            )

            # Записываем в user_data измененное сообщение для синхронизации данных
            user_data[cls.CONV_NAME].message = edited_conv_message
        
        # Устанавливаем в user_data обработчик, который обработает следующий update от пользователя
        user_data[cls.CONV_NAME].state = cls.FULL_NAME

        return cls.FULL_NAME

    @classmethod
    async def full_name_handler(cls, update: Update, context: ContextTypes.DEFAULT_TYPE, error_text: str = None, from_prev_state: bool = False) -> int:
        bot = context.bot
        user_data = context.user_data

        # Если в функцию передан текст ошибки пользователя,
        # это значит, что диалог уже был ранее начат
        if error_text is not None:
            from_prev_state = True

        if not from_prev_state:
            # Сюда попадаем в случае перехода на это состояние в обычной последовательности

            # Сохраняем полученные данные в user_data
            try:
                user_data[cls.CONV_NAME].data.applicant.full_name = update.effective_message.text
            except ValueError:
                await cls.start_conversation(update=update, context=context, error_text='Вы ввели некорректное ФИО')
                return cls.FULL_NAME
            finally:        
                # Удаляем сообщение от пользователя
                await update.effective_message.delete()

        # Текст следуюего состояния
        message_text = cls._get_message_text(
            user_data=user_data,
            state_text='Введите номер СПО абитуриента в формате СПО000123(Д)'
        )

        await bot.edit_message_text(
            text=message_text,
            chat_id=update.effective_chat.id,
            message_id=user_data[cls.CONV_NAME].message.id,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[cls.PREV_STATE_INLINE_BUTTON], [cls.CANCEL_INLINE_BUTTON]])
        )

        # Устанавливаем в user_data обработчик, который обработает следующий update от пользователя
        user_data[cls.CONV_NAME].state = cls.SPO_NUMBER

        return cls.SPO_NUMBER

    @classmethod
    async def spo_number_handler(cls, update: Update, context: ContextTypes.DEFAULT_TYPE, error_text: str = None, from_prev_state: bool = False) -> int:
        bot = context.bot
        user_data = context.user_data

        # Если в функцию передан текст ошибки пользователя,
        # это значит, что диалог уже был ранее начат
        if error_text is not None:
            from_prev_state = True

        if not from_prev_state:
            # Сюда попадаем в случае перехода на это состояние в обычной последовательности

            # Сохраняем полученные данные в user_data
            user_data[cls.CONV_NAME].data.spo_number = update.effective_message.text

            # Удаляем сообщение от пользователя
            await update.effective_message.delete()
        
        # Текст следуюего состояния
        message_text = cls._get_message_text(
            user_data=user_data,
            state_text='Выберите, каким способом абитуриент подал документы, нажав на одну из кнопок ниже'
        )

        await bot.edit_message_text(
            text=message_text,
            chat_id=update.effective_chat.id,
            message_id=user_data[cls.CONV_NAME].message.id,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text='Очно', callback_data=cls.CONV_NAME + '_submit_method_personally'),
                        InlineKeyboardButton(text='Онлайн', callback_data=cls.CONV_NAME + '_submit_method_online')
                    ],
                    [cls.PREV_STATE_INLINE_BUTTON],
                    [cls.CANCEL_INLINE_BUTTON]
                ]
            )
        )

        # Устанавливаем в user_data обработчик, который обработает следующий update от пользователя
        user_data[cls.CONV_NAME].state = cls.SUBMIT_METHOD

        return cls.SUBMIT_METHOD

    @classmethod
    async def submit_method_handler(cls, update: Update, context: ContextTypes.DEFAULT_TYPE, error_text: str = None, from_prev_state: bool = False) -> int:
        bot = context.bot
        user_data = context.user_data

        # Если в функцию передан текст ошибки пользователя,
        # это значит, что диалог уже был ранее начат
        if error_text is not None:
            from_prev_state = True

        if not from_prev_state:
            # Сюда попадаем в случае перехода на это состояние в обычной последовательности

            await update.callback_query.answer()

            # Сохраняем полученные данные в user_data
            match update.callback_query.data.split('_')[-1]:
                case 'personally':
                    user_data[cls.CONV_NAME].data.submit_method = 'Очно'

                case 'online':
                    # Если абитуриент подал докменты онлайн, то пропускаем шаг с оригиналом документа об образовании
                    user_data[cls.CONV_NAME].data.submit_method = 'Онлайн'

                    message_text = cls._get_message_text(
                        user_data=user_data,
                        state_text='Проверьте введённые данные и в случае их корректности нажмите на кнопку «Подтвердить» для их сохранения, или отмените действие, нажав на соответствующую кнопку ниже'
                    )

                    await bot.edit_message_text(
                        text=message_text,
                        chat_id=update.effective_chat.id,
                        message_id=user_data[cls.CONV_NAME].message.id,
                        parse_mode='HTML',
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [cls.CONFIRM_INLINE_BUTTON],
                                [cls.CANCEL_INLINE_BUTTON]
                            ]
                        )
                    )

                    # Устанавливаем в user_data обработчик, который обработает следующий update от пользователя
                    user_data[cls.CONV_NAME].state = cls.CONFIRM

                    return cls.CONFIRM

        # Текст следуюего состояния
        message_text = cls._get_message_text(
            user_data=user_data,
            state_text='Укажите, сдал ли абитуриент оригинал документа об образовании, нажав на одну из кнопок ниже'
        )

        await bot.edit_message_text(
            text=message_text,
            chat_id=update.effective_chat.id,
            message_id=user_data[cls.CONV_NAME].message.id,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text='Да', callback_data=cls.CONV_NAME + '_original_certificate_true'),
                        InlineKeyboardButton(text='Нет', callback_data=cls.CONV_NAME + '_original_certificate_false')
                    ],
                    [cls.PREV_STATE_INLINE_BUTTON],
                    [cls.CANCEL_INLINE_BUTTON]
                ]
            )
        )

        # Устанавливаем в user_data обработчик, который обработает следующий update от пользователя
        user_data[cls.CONV_NAME].state = cls.ORIGINAL_CERTIFICATE

        return cls.ORIGINAL_CERTIFICATE

    @classmethod
    async def original_certificate_handler(cls, update: Update, context: ContextTypes.DEFAULT_TYPE, error_text: str = None, from_prev_state: bool = False) -> int:
        bot = context.bot
        user_data = context.user_data

        # Если в функцию передан текст ошибки пользователя,
        # это значит, что диалог уже был ранее начат
        if error_text is not None:
            from_prev_state = True

        if not from_prev_state:
            # Сюда попадаем в случае перехода на это состояние в обычной последовательности

            # Сохраняем полученные данные в user_data
            if update.callback_query.data.split('_')[-1] == 'true':
                user_data[cls.CONV_NAME].data.original_certificate = True
            else:
                user_data[cls.CONV_NAME].data.original_certificate = False
            
            await update.callback_query.answer()
        
        # Текст следуюего состояния
        message_text = cls._get_message_text(
            user_data=user_data,
            state_text='Проверьте введённые данные и в случае их корректности нажмите на кнопку «Подтвердить» для их сохранения, или отмените действие, нажав на соответствующую кнопку ниже'
        )

        await bot.edit_message_text(
            text=message_text,
            chat_id=update.effective_chat.id,
            message_id=user_data[cls.CONV_NAME].message.id,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(
                [
                    [cls.CONFIRM_INLINE_BUTTON],
                    [cls.CANCEL_INLINE_BUTTON]
                ]
            )
        )

        # Устанавливаем в user_data обработчик, который обработает следующий update от пользователя
        user_data[cls.CONV_NAME].state = cls.CONFIRM

        return cls.CONFIRM

    @classmethod
    async def confirm_handler(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        bot = context.bot
        user_data = context.user_data

        await update.callback_query.answer()

        message_text = cls._get_message_text(user_data=user_data)

        await bot.edit_message_text(
            text=message_text + f'{chr(0x23F3)} Сохранение данных...',
            chat_id=update.effective_chat.id,
            message_id=user_data[cls.CONV_NAME].message.id,
            parse_mode='HTML'
        )

        save_result = await cls.save_application(cls=cls, bot=bot, application=user_data[cls.CONV_NAME].data)

        if save_result:
            await bot.edit_message_text(
                text=message_text + f'{chr(0x2705)} Данные сохранены',
                chat_id=update.effective_chat.id,
                message_id=user_data[cls.CONV_NAME].message.id,
                parse_mode='HTML'
            )
        else:
            await bot.edit_message_text(
                text=message_text + f'{chr(0x274C)} При сохранении данных произошла ошибка {chr(0x1F614)}. Попробуйте ещё раз',
                chat_id=update.effective_chat.id,
                message_id=user_data[cls.CONV_NAME].message.id,
                parse_mode='HTML'
            )

        return ConversationHandler.END

    async def save_application(cls, bot, application: Application) -> bool:
        await asyncio.sleep(5)
        return True

    @classmethod
    def get_handler_by_name(cls, name: str):
        return getattr(cls, name)

    @classmethod
    def _get_message_text(cls, user_data, state_text: str = '', error_text: str = None) -> str:
        application = user_data[cls.CONV_NAME].data
        message_text = f'{chr(0x2709)} <b>Отправка заявления</b> {chr(0x2709)}\n\n'

        if application is not None:
            if application.applicant.full_name is not None:
                message_text += f'{chr(0x1F464)} <b>ФИО:</b> {application.applicant.full_name}\n'

            if application.spo_number is not None:
                message_text += f'{chr(0x1FAAA)} <b>Номер СПО:</b> {application.spo_number}\n'

            if application.submit_method is not None:
                message_text += f'{chr(0x1F4AC )} <b>Способ подачи:</b> {application.submit_method}\n'

            if application.original_certificate is not None:
                message_text += f'{chr(0x1F39F)} <b>Сдан оригинал:</b> '

                if application.original_certificate:
                    message_text += f'Да {chr(0x26A0) + chr(0xFE0F)}\n'
                else:
                    message_text += f'Нет {chr(0x1F60C)}\n'

            # Проверяем, есть ли двойной отступ после данных
            if message_text[-1] == '\n' and message_text[-2] != '\n':
                message_text += '\n'
        
        if error_text is not None:
            message_text += f'{chr(0x2757)} <b>Ошибка:</b> {error_text}'

            if error_text in user_data[cls.CONV_NAME].message.text:
                # Сюда попадаем в случае, если в функцию передан текст ошибки,
                # который уже есть в тексте сообщения, то есть если ошибка идентичная

                # Опредеяем регулярное выражение для поиска счетчика ошибки в сообщении
                # ВАЖНО: в счетчике используется ИМЕННО символ умножения, поэтому он вынесен в константу,
                # данный символ не эквивалентен латинской букве «x» или кириллической «х»
                counter_pattern = r'\(' + cls.MULTIPLICATION_SIGN + r'\d+\)$'

                # Получаем объект сопоставления counter_pattern с текстом сообщения,
                # который может содержать данные о совдаениях и их расположениях
                # или же равняться None в случае их отсутствия
                # Обязательно используем флаг MULTILINE для поддержки многострочности,
                # ибо counter_pattern написан так, что ищет счетчик в конце строк (об этом говорит спецсимвол $),
                # поэтому данный флаг говорит функции, чтобы она искала в конце всех строк, а не всего текста
                match = re.search(pattern=counter_pattern, string=user_data[cls.CONV_NAME].message.text, flags=re.MULTILINE)

                if match is None:
                    # Сюда попадаем в случае, если в тексте сообщения не найдено сопоставлений с counter_pattern,
                    # то есть в тексте нет счетка ошибки, а значит сейчас она появилась второй раз,
                    # поэтому счетчик начинаем с двух

                    message_text += f' ({cls.MULTIPLICATION_SIGN}2)'
                else:
                    # Сюда попадаем в случае нахождения в тексте сообщения сопоставлений с counter_pattern,
                    # то есть в тексте имеется счетчик ошибок, который был начат ранее.
                    
                    # Получаем текущее значение счетчика, которое записано в сообщении
                    # СПРАВКА: метод group() у объекта сопоставления возвращает список из
                    # совпадений с counter_pattern, ибо подразумевается, что совпадений с counter_pattern может быть несколько,
                    # в данном же случае совпадение только одно, поэтому метод вернет именно строку, а не список
                    current_error_count = int(match.group()[2:-1])
                    
                    # Увеличиваем счетник на 1, заменяя найденное совпадение с counter_pattern на новый текст счетчика
                    # Здесь обязательно берем у Message атрибут text_html, а не просто text, чтобы не пропало форматирование
                    message_text = re.sub(
                        pattern=counter_pattern,
                        repl=f'({cls.MULTIPLICATION_SIGN}{current_error_count+1})',
                        string=user_data[cls.CONV_NAME].message.text_html,
                        flags=re.MULTILINE
                    )
            
            message_text += '\n\n'

        # Проверяем, нет ли уже в тексте сообщения текста состояния,
        # ибо при изменении счетчика мы меняем именно текст объекта Message,
        # в котором уже есть текст состояния, та как он был вставлен при
        # при первом заходе в это состояние
        if state_text not in message_text:
            message_text += state_text

        return message_text
