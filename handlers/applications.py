from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

from datetime import datetime

import utils

from constants import GENERIC_CHAT, ONLINE_THREAD_ID, FRONT_THREAD_ID, OTK_THREAD_ID


def send_application(message: Message, bot: TeleBot):
    bot.send_message(message.chat.id, 'Вы начали процесс отправки заявления.')
    get_applicant_fullname(message=message, bot=bot)


def get_applicant_fullname(message: Message, bot: TeleBot, snils_from_otk: int = None, is_from_otk: bool = False, is_spo: bool = False):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Отмена'))

    msg = bot.send_message(message.chat.id, "Введите ФИО абитуриента.", reply_markup=rmk)
    bot.register_next_step_handler(msg, get_applicant_snils, bot=bot, snils_from_otk=snils_from_otk, is_from_otk=is_from_otk, is_spo=is_spo)


def get_applicant_snils(message: Message, bot: TeleBot, snils_from_otk: int = None, is_from_otk: bool = False, is_spo: bool = False):
    applicant_fullname = utils.is_correct_person_name(message.text)

    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        
        bot.send_message(message.chat.id, 'Отправка заявления отменена.', reply_markup=rmk)
        return
    
    if not applicant_fullname: 
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неккоректное ФИО абитуриента.\nВведите корректное ФИО.'),
            get_applicant_snils,
            bot=bot, snils_from_otk=snils_from_otk, is_from_otk=is_from_otk, is_spo=is_spo
        )
        return
    
    if is_from_otk:
        get_application_type(message=message, bot=bot, applicant_fullname=applicant_fullname, snils_from_otk=snils_from_otk, is_from_otk=is_from_otk, is_spo=is_spo)
        return

    msg = bot.send_message(message.chat.id, 'Введите СНИЛС или номер СПО абитуриента.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00\nНомер СПО в формате:\nСПО000111</code>')
    bot.register_next_step_handler(msg, get_application_type, bot=bot, applicant_fullname=applicant_fullname, is_spo=is_spo)


def get_application_type(message: Message, bot: TeleBot, applicant_fullname, snils_from_otk: int = None, is_from_otk: bool = False, is_spo: bool = False):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Отмена'))
    
    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        
        bot.send_message(message.chat.id, 'Отправка заявления отменена.', reply_markup=rmk)
        return

    if is_from_otk:
        applicant_snils = snils_from_otk
    else:
        if message.text[:3] == 'СПО':
            is_spo = True
            applicant_snils = message.text
        else:
         applicant_snils = message.text.replace('-', '').replace(' ', '')

    if ((not applicant_snils.isdigit()) or len(applicant_snils) != 11) and not is_spo:
        msg = bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неккоректный номер СНИЛС или СПО.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00\nНомер СПО в формате:\nСПО000111</code>',reply_markup=rmk)
        bot.register_next_step_handler(msg, get_application_type, bot=bot, applicant_fullname=applicant_fullname)
        return
    
    employee = bot.db.get_employee_data(message.from_user.id)
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Продолжить'), KeyboardButton('Отмена'))
    
    if not applicant_fullname:
        msg = bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Недостаточно данных.\n\n<i>Корректный формат:</i>\n<code>Иванов Иван Иванович</code>')
        bot.register_next_step_handler(msg, get_application_type, applicant_fullname=applicant_fullname, bot=bot)
        return
    if bot.db.is_emloyee_has_permission(employee_id=message.from_user.id, permissions=['ОТК', 'FrontLine']):
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Очно'), KeyboardButton('Онлайн'))
        rmk.add(KeyboardButton('Отмена'))
        bot.register_next_step_handler(
            bot.send_message(message.from_user.id, 'Выберете способ подачи документов.', reply_markup=rmk),
            get_delivery_method,
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
        )
    elif employee['department'] == 'Онлайн-заявления':
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Вы отправляете информацию об онлайн-заявлении.', reply_markup=rmk), 
            get_status_in_pk, 
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
        )
        return
    elif employee['department'] == 'FrontLine':
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Вы отправляете информацию об очном заявлении.', reply_markup=rmk), 
            is_passed_original_certificate, 
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk = is_from_otk, is_spo=is_spo
        )
        return
    else:
        bot.send_message(message.chat.id, 'Произошла неизвестная ошибка отдела.\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>')
    

def get_delivery_method(message: Message, applicant_snils, applicant_fullname, bot: TeleBot, is_from_otk: bool = False, is_spo: bool = False):
    delivery_method = message.text
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Продолжить'), KeyboardButton('Назад'))
    
    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))

        bot.send_message(message.chat.id, 'Отправка заявления отменена.', reply_markup=rmk)
        return

    if delivery_method == 'Очно':
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Вы отправляете информацию об очном заявлении.', reply_markup=rmk), 
            is_passed_original_certificate, 
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
        )
    elif delivery_method == 'Онлайн':
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Вы отправляете информацию об онлайн-заявлении.', reply_markup=rmk), 
            get_status_in_pk, 
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk = is_from_otk, is_spo=is_spo
        )
    else:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Очно'), KeyboardButton('Онлайн'))
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неверный способ подачи документов.\nВыберите из доступных:', reply_markup=rmk),
            get_delivery_method,
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk = is_from_otk, is_spo=is_spo
        )
        return


def get_status_in_pk(message: Message, applicant_snils, applicant_fullname, bot: TeleBot, is_from_otk: bool = False, is_spo: bool = False):
    if message.text == 'Назад' and bot.db.is_emloyee_has_permission(employee_id=message.from_user.id, permissions=['admin']):
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Очно'), KeyboardButton('Онлайн'))
        bot.register_next_step_handler(
            bot.send_message(message.from_user.id, 'Выберете способ подачи документов.', reply_markup=rmk),
            get_delivery_method,
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
        )
        return
    
    if message.text == "Отмена":
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        bot.send_message(message.chat.id, 'Отправка заявления отменена.', reply_markup=rmk)
        return

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Принято'), KeyboardButton('Отклонено'))
    rmk.add(KeyboardButton('Отмена'))
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберите статус заявления в ПК.', reply_markup=rmk),
        get_application_deny_reason,
        applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
    )
    

def get_application_deny_reason(message: Message, applicant_snils, applicant_fullname, bot: TeleBot, is_from_otk: bool = False, is_spo: bool = False):
    application_status = message.text
    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        
        bot.send_message(message.chat.id, 'Отправка заявления отменена.')
        return

    if application_status == 'Принято':
        message_datetime_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')
        employee = bot.db.get_employee_data(message.from_user.id)
        
        result = bot.db.send_online_application(
            snils=applicant_snils, 
            applicant_surname=applicant_fullname[0], 
            applicant_name=applicant_fullname[1], 
            applicant_patronymic=applicant_fullname[2],
            employee_id=message.from_user.id,
            status=application_status,
            deny_reason='',
            datetime=message.date,
            is_spo=is_spo
        )

        if result:
            message_text = f'<code>[{message_datetime_str}]</code>\n✅ Сотрудник <b>{employee["name"]} {employee["surname"]}</b> принял заявление.\n'
            message_text += f'🌐 Способ подачи заявления: Онлайн\n'
            if is_spo:
                message_text += f'🪪 Номер СПО абитуриента: {applicant_snils}.\n'
            else:
                message_text += f'🪪 СНИЛС абитуриента: {utils.snils_to_str(applicant_snils)}.\n'
            message_text += f'👤 ФИО абитуриента: {applicant_fullname[0]} {applicant_fullname[1]}{f" {applicant_fullname[2]}" if applicant_fullname[2] else ""}.'
            bot.send_message(GENERIC_CHAT, message_text, message_thread_id=ONLINE_THREAD_ID)
            
            rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
            bot.send_message(message.chat.id, 'Информация направлена в общий чат.', reply_markup=rmk) 
        else:
            bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>')
        
        if is_from_otk:
            bot.send_message(message.chat.id, '<code>Перенаправление на проверку дела ОТК.</code>')
            check_if_application_is_right_to_check_file(message=None, bot=bot, is_from_send=True, applicant_snils=applicant_snils, is_spo=is_spo)
            return

    
    elif application_status == 'Отклонено':
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите причину отклонения заявления.'),
            send_online_denied_application,
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
        )
        return
    
    else:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Принято'), KeyboardButton('Отклонено'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Выберете корректный статус завления в ПК.', reply_markup=rmk),
            get_application_deny_reason,
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
        )
        return


def send_online_denied_application(message: Message, applicant_snils, applicant_fullname, bot: TeleBot, is_from_otk: bool = False, is_spo: bool = False):
    deny_reason = message.text
    
    message_datetime_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')
    employee = bot.db.get_employee_data(message.from_user.id)

    result = bot.db.send_online_application(
        snils=applicant_snils, 
        applicant_surname=applicant_fullname[0], 
        applicant_name=applicant_fullname[1], 
        applicant_patronymic=applicant_fullname[2],
        employee_id=message.from_user.id,
        status='Отклонено',
        deny_reason=deny_reason,
        datetime=message.date,
        is_spo=is_spo
    )
    
    if result:
        message_text = f'<code>[{message_datetime_str}]</code>\n📛 Сотрудник <b>{employee["name"]} {employee["surname"]}</b> отклонил заявление.\n'
        message_text += f'🌐 Способ подачи заявления: Онлайн\n'
        if is_spo:
            message_text += f'🪪 Номер СПО абитуриента: {applicant_snils}.\n'
        else: 
            message_text += f'🪪 СНИЛС абитуриента: {utils.snils_to_str(applicant_snils)}.\n'
        message_text += f'👤 ФИО абитуриента: {applicant_fullname[0]} {applicant_fullname[1]}{f" {applicant_fullname[2]}" if applicant_fullname[2] else ""}.'
        message_text += f'\n⚠️ Причина отклонения заявления: {deny_reason}'
        bot.send_message(GENERIC_CHAT, message_text, message_thread_id=ONLINE_THREAD_ID)
        
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        bot.send_message(message.chat.id, 'Информация направлена в общий чат.', reply_markup=rmk)
        
        if is_from_otk:
            bot.send_message(message.chat.id, '<code>Перенаправление на проверку дела ОТК.</code>')
            check_if_application_is_right_to_check_file(message=None, bot=bot, is_from_send=True, applicant_snils=applicant_snils, is_spo=is_spo)
            return
    else:
        bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>')  

    

def is_passed_original_certificate(message: Message, applicant_snils, applicant_fullname, bot: TeleBot, is_from_otk: bool = False, is_spo: bool = False):
    if message.text == 'Назад' and bot.db.is_emloyee_has_permission(employee_id=message.from_user.id, permissions=['admin']):
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Очно'), KeyboardButton('Онлайн'))
        bot.register_next_step_handler(
            bot.send_message(message.from_user.id, 'Выберете способ подачи документов.', reply_markup=rmk),
            get_delivery_method,
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname
        )
        return
    
    if message.text == "Отмена":
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        bot.send_message(message.chat.id, 'Отправка заявления отменена.', reply_markup=rmk)
        return
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
    
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Сдал ли абитуриент оригнал аттестата?', reply_markup=rmk),
        send_personal_application, 
        applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, bot=bot, is_from_otk=is_from_otk, is_spo=is_spo
    )


def send_personal_application(message: Message, applicant_snils, applicant_fullname, bot: TeleBot, is_from_otk: bool = False, is_spo: bool = False):
    is_original = message.text

    if is_original not in ['Да', 'Нет']:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Вы указали неккоретную информацию. Выберете ответ из предложенных вариантов.'),
            is_passed_original_certificate,
            applicant_snils = applicant_snils, applicant_fullname = applicant_fullname, is_spo=is_spo
        )
    
    if is_original == 'Да':
        is_original = 1
    else:
        is_original = 0

    result = bot.db.send_person_applicate(
        snils=applicant_snils, 
        applicant_surname=applicant_fullname[0], 
        applicant_name=applicant_fullname[1], 
        applicant_patronymic=applicant_fullname[2],
        employee_id=message.from_user.id,
        datetime=message.date,
        passed_original_certificate=is_original,
        is_spo=is_spo
    )
    
    if result:
        message_datetime_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')
        employee = bot.db.get_employee_data(message.from_user.id)
        message_text = f'<code>[{message_datetime_str}]</code>\n✅ Сотрудник <b>{employee["name"]} {employee["surname"]}</b> принял заявление.\n'
        message_text += f'🏢 Способ подачи заявления: Очно\n'
        if is_spo:
            message_text += f'🪪 Номер СПО абитуриента: {applicant_snils}.\n'
        else:
            message_text += f'🪪 СНИЛС абитуриента: {utils.snils_to_str(applicant_snils)}.\n'
        message_text += f'👤 ФИО абитуриента: {applicant_fullname[0]} {applicant_fullname[1]}{f" {applicant_fullname[2]}" if applicant_fullname[2] else ""}.\n'
        message_text += f'📕 Оригинал аттестата: {"Сдан. 🟢" if is_original == 1 else "Не сдан. 🔴"}'
        bot.send_message(GENERIC_CHAT, message_text, message_thread_id=FRONT_THREAD_ID)
        
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        bot.send_message(message.chat.id, 'Информация направлена в общий чат.', reply_markup=rmk)
        
        if is_from_otk:
            bot.send_message(message.chat.id, '<code>Перенаправление на проверку дела ОТК.</code>')
            check_if_application_is_right_to_check_file(message=message, bot=bot, is_from_send=True, applicant_snils=applicant_snils, is_spo=is_spo)
            return
    else:
        bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>')  


def select_applicaton_to_update_certificate_status(message: Message, bot: TeleBot):
    if bot.db.is_emloyee_has_permission(message.from_user.id, ['FrontLine', 'Ресепшн', 'ОТК']):
        bot.send_message(message.chat.id, 'Вы обновляете данные о наличии оригинала аттестата абитуриента.')
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите СНИЛС или номер СПО абитуриента.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00\nНомер СПО в формате:\nСПО000123</code>'),
            check_if_application_to_update_certificate_status_is_correct,
            bot=bot
        )


def check_if_application_to_update_certificate_status_is_correct(message: Message, bot: TeleBot):
    is_spo=False
    
    if message.text[:3] == 'СПО':
        is_spo = True
        applicant_snils = message.text
    else:
        applicant_snils = message.text.replace('-', '').replace(' ', '')
    
    if ((not applicant_snils.isdigit()) or len(applicant_snils) != 11) and not is_spo:
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неккоректный номер СНИЛС.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00</code>'),
            select_applicaton_to_update_certificate_status,
            bot=bot
        )
        return
    
    variant_applications_to_update = bot.db.get_applicant_data_via_snils(applicant_snils, is_spo)
    
    if variant_applications_to_update == None:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Отмена'))
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '❌ <b>Информация не найдена!</b>\nВведите ФИО абитуриента.', reply_markup=rmk),
            get_applicant_fullname,
            message=message, bot=bot, snils_from_otk=applicant_snils, is_from_otk=True, is_spo=is_spo
        )
        return

    msg = f'<i>ФИО абитуриента:</i>\n📍 {bot.db.get_applicant_fullname_via_id(application_id=variant_applications_to_update["id"])["applicant_fullname"]}\n'
    msg += f'\n<i>Способ подачи документов:</i>\n📍 {variant_applications_to_update["submit_method"]}\n'
    msg += f'\n<i>Ответственный сотрудник:</i>\n 📍 {variant_applications_to_update["employee_fullname"]}\n'
    
    process_datetime_str = datetime.fromtimestamp(variant_applications_to_update["datetime"]).strftime('%d.%m.%Y %H:%M:%S')
    
    msg += f'\n<i>Дата обработки:</i>\n 📍 {process_datetime_str}'

    bot.send_message(message.from_user.id, msg)

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
    rmk.add(KeyboardButton('Отмена'))

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Данные соответсвуют действительности?', reply_markup=rmk),
        get_type_action_to_update_certificate_status,
        application_id = variant_applications_to_update['id'], bot=bot, is_spo=is_spo
    )

def get_type_action_to_update_certificate_status(message: Message, application_id, bot: TeleBot, is_spo):
    ans = message.text

    if ans == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Внести аттестат'))
        bot.send_message(message.chat.id, 'Внесение данных отменено.', reply_markup=rmk)
        return
    elif ans == 'Нет':
        msg = f'<b>Ошибка в номере СНИЛС.</b>\nПовторите попытку ввода.\n'
        msg += f'<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00</code>\n\n'
        msg += f'<code>Либо номер СПО, в формате СПО000123</code>'
        msg += f'Если Вы уверены в достоверности номера СНИЛС, обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>'

        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, msg, reply_markup=rmk),
            check_if_application_to_update_certificate_status_is_correct,
            bot=bot,
        )
        return
    elif ans == 'Да':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Принять аттестат'), KeyboardButton('Вернуть аттестат'))
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Выберите действие.', reply_markup=rmk),
            update_certificate_status,
            application_id=application_id, bot=bot, is_spo=is_spo
        )
    else:
        rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неккоректный ответ.\nДанные соответсвуют действительности?', reply_markup=rmk),
            get_type_action_to_update_certificate_status,
            application_id = application_id, bot=bot, is_spo=is_spo
        )


def update_certificate_status(message: Message, application_id, bot: TeleBot, is_spo: bool = False):
    message_datetime_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')
    employee = bot.db.get_employee_data(employee_id=message.from_user.id)
    applicant_data = bot.db.get_applicant_data_via_id(application_id=application_id)

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Внести аттестат'))

    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Внесение данных отменено.', reply_markup=rmk)
        return
    
    action_type = 1 if message.text == 'Принять аттестат' else 0
    
    result = bot.db.send_info_about_passed_original_certificate(
        applicantion_id=application_id,
        passed_original_certificate_status=action_type,
        responsible_employee_id=message.from_user.id
    )
    if result:
        bot.send_message(message.from_user.id, 'Данные успешно обновлены.', reply_markup=rmk)
        
        message_text = f'<code>[{message_datetime_str}]</code>\n🔄 Сотрудник <b>{employee["name"]} {employee["surname"]}</b> обновил информацию о наличии оригинала аттестата.\n'
        message_text += f'🪪 СНИЛС/СПО абитуриента: {utils.snils_to_str(applicant_data["snils"]) if applicant_data["snils"] is not None else applicant_data["spo_number"]}.\n'
        message_text += f'👤 ФИО абитуриента: {bot.db.get_applicant_fullname_via_id(application_id=application_id)["applicant_fullname"]}.\n'
        message_text += f'📕 Оригинал аттестата: {"Сдан. 🟢" if action_type == 1 else "Не сдан. 🔴"}'
        bot.send_message(GENERIC_CHAT, message_text, message_thread_id=OTK_THREAD_ID)
    else:
        bot.send_warn(f'При попытке обновить данные о наличии оригинала аттестата у сотрудника отдела {employee["department"]},\nФИО: {employee["surname"]} {employee["name"]} произошла ошибка.\nОбратиться: {message.from_user.username}')
        bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk)  


def select_file_to_check(message: Message, bot: TeleBot):
    if bot.db.is_emloyee_has_permission(message.from_user.id, ['ОТК', 'FrontLine',]):
        bot.send_message(message.chat.id, 'Вы проверяете личное дело абитуриента.')
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите СНИЛС абитуриента.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00\nЛибо номер СПО абитуриента в формате СПО000123(Д)</code>'),
            check_if_application_is_right_to_check_file, 
            bot=bot
        )
    else:
        bot.send_message(message.chat.id, 'Ошибка! Данная команда доступна только отделу ОТК.')
        return

def check_if_application_is_right_to_check_file(message: Message, bot: TeleBot, is_from_send: bool = False, applicant_snils: int = 0, is_spo: bool = False):
    if message.text == 'Отмена':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
        
        bot.send_message(message.chat.id, 'Проверка заявления отменена.', reply_markup=rmk)
        return
    
    if is_from_send:
        applicant_snils = applicant_snils
    else:
        if message.text[:3] == 'СПО':
            is_spo = True
            applicant_snils = message.text
        else:
         applicant_snils = message.text.replace('-', '').replace(' ', '')

    if ((not applicant_snils.isdigit()) or len(applicant_snils) != 11) and not is_spo:
        msg = bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неккоректный номер СНИЛС.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00</code>')
        bot.register_next_step_handler(msg, check_if_application_is_right_to_check_file, bot=bot)
        return
    
    variant_applications_to_update = bot.db.get_applicant_data_via_snils(applicant_snils, is_spo)
    
    if variant_applications_to_update is None:
            rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Отправить заявление'))
            bot.register_next_step_handler(
                bot.send_message(message.chat.id, '❌ <b>Информация не найдена! Пожалуйста, внесите данное заявление.</b>\nВведите ФИО абитуриента'),
                get_applicant_snils,
                bot=bot, snils_from_otk=applicant_snils, is_from_otk=True, is_spo=is_spo
            )
            return
    
    msg = f'<b>Основная информация об абитуриенте: </b>\n'
    msg += f'<i>ФИО абитуриента:</i>\n📍 {bot.db.get_applicant_fullname_via_id(application_id=variant_applications_to_update["id"])["applicant_fullname"]}\n'
    msg += f'\n<i>Способ подачи документов:</i>\n📍 {variant_applications_to_update["submit_method"]}\n'
    
    certificate_status = "Сдан. 🟢" if variant_applications_to_update["passed_original_certificate"] == 1 else "Не сдан. 🔴"
    msg += f'\n<i>Наличие оригинала аттестата:</i>\n📍 {certificate_status}'
    msg += f'\n\n<i>Ответственный сотрудник:</i>\n 📍 {variant_applications_to_update["employee_fullname"]}\n'
    
    process_datetime_str = datetime.fromtimestamp(variant_applications_to_update["datetime"]).strftime('%d.%m.%Y %H:%M:%S')
    msg += f'\n<i>Дата обработки:</i>\n 📍 {process_datetime_str}'
    msg += f'\nПроверено сотрудником ОТК:\n 📍 {"Проверено" if variant_applications_to_update["status_otk"] else "Не проверено"}'

    bot.send_message(message.from_user.id, msg)
    bot.send_message(message.from_user.id, '<b>Помните, что вы сверяетесь с КАС! Не с информацией в боте!</b>\n<i>Однако, при наличии ошибок в информации в боте, указывайте их далее.</i>')

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
    rmk.add(KeyboardButton('Отмена'))

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Данные соответсвуют действительности?', reply_markup=rmk),
        check_is_application_correct_to_check_file,
        application_id = variant_applications_to_update['id'], bot=bot
    )

def check_is_application_correct_to_check_file(message: Message, application_id, bot: TeleBot):
    ans = message.text
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Проверить дело'))
    
    if ans == 'Отмена':
        bot.send_message(message.chat.id, 'Проверка заявления отменена.', reply_markup=rmk)
        return
    elif ans == 'Нет':
        msg = f'<b>Ошибка в номере СНИЛС.</b>\nПовторите попытку ввода.\n'
        msg += f'<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00</code>\n\n'
        msg += f'Если Вы уверены в достоверности номера СНИЛС, обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>'

        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, msg, reply_markup=rmk),
            check_if_application_is_right_to_check_file,
            bot=bot
        )
        return
    elif ans == 'Да':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Найдены ли ошибки в личном деле?', reply_markup=rmk),
            is_errors_in_file,
            application_id=application_id, bot=bot
        )
    else:
        rmk.add(KeyboardButton('Да'), KeyboardButton('Нет'))
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неккоректный ответ.\nДанные соответсвуют действительности?', reply_markup=rmk),
            get_type_action_to_update_certificate_status,
            application_id = application_id, bot=bot
        )


def is_errors_in_file(message: Message, application_id, bot: TeleBot):
    message_datetime_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')
    applicant_data = bot.db.get_applicant_data_via_id(application_id=application_id)
    employee = bot.db.get_employee_data(employee_id=message.from_user.id)
    employee_first = bot.db.get_employee_data(applicant_data['employee_id'])

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Проверить дело'))

    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Внесение данных отменено.', reply_markup=rmk)
        return
    
    if message.text == 'Нет':
        result = bot.db.send_check_application_file(
            otk_employee_id=message.from_user.id,
            has_errors_otk=0,
            datetime_otk_check=message.date,
            application_id=application_id
        )
        
        if result:
            message_text = f'<code>[{message_datetime_str}]</code>\n🛂 Сотрудник <b>{employee["name"]} {employee["surname"]}</b> проверил личное дело абитуриента.\n'
            message_text += f'🪪 СНИЛС/СПО абитуриента: {utils.snils_to_str(applicant_data["snils"])}.\n'
            message_text += f'👤 ФИО абитуриента: {bot.db.get_applicant_fullname_via_id(application_id=application_id)["applicant_fullname"]}.\n'
            message_text += f'✅ Ошибки: не найдены'
            message_text += f'\n👨‍💼 Принял заявление: сотудник отдела {employee_first["department"]}, {employee_first["name"]} {employee_first["surname"]}\n'
            bot.send_message(GENERIC_CHAT, message_text, message_thread_id=OTK_THREAD_ID)
            
            bot.send_message(message.from_user.id, 'Информация о проверке направлена в общий чат.', reply_markup=rmk)
        else:
            bot.send_warn(f'При попытке проверить личное дело абитуриента {bot.db.get_applicant_fullname_via_id(application_id=application_id)["applicant_fullname"]} у сотрудника отдела {employee["department"]},\nФИО: {employee["surname"]} {employee["name"]} произошла ошибка.\nОбратиться: {message.from_user.username}')
            bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
    
    elif message.text == 'Да':
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Отмена'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Введите информацию об ошибках в личном деле, либо отмените действие.', reply_markup=rmk),
            get_otk_errors,
            application_id = application_id, bot=bot
        )

def get_otk_errors(message: Message, application_id, bot: TeleBot):
    errors_otk = message.text
    message_datetime_str = datetime.fromtimestamp(message.date).strftime('%d.%m.%Y %H:%M:%S')
    
    applicant_data = bot.db.get_applicant_data_via_id(application_id=application_id)
    employee = bot.db.get_employee_data(employee_id=message.from_user.id)
    employee_first = bot.db.get_employee_data(applicant_data['employee_id'])

    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Проверить дело'))

    if message.text == 'Отмена':
        bot.send_message(message.chat.id, 'Внесение данных отменено.', reply_markup=rmk)
        return
    
    result = bot.db.send_check_application_file(
            otk_employee_id=message.from_user.id,
            has_errors_otk=1,
            errors_otk = errors_otk,
            datetime_otk_check=message.date,
            application_id=application_id
        )
    
    if result:
        message_text = f'<code>[{message_datetime_str}]</code>\n🛂 Сотрудник <b>{employee["name"]} {employee["surname"]}</b> проверил личное дело абитуриента.\n'
        message_text += f'🪪 СНИЛС/СПО абитуриента: {utils.snils_to_str(applicant_data["snils"])}.\n'
        message_text += f'👤 ФИО абитуриента: {bot.db.get_applicant_fullname_via_id(application_id=application_id)["applicant_fullname"]}.\n'
        message_text += f'📛 Ошибки: найдены\n'
        message_text += f'📍 Список ошибок:\n{errors_otk}'
        message_text += f'\n👨‍💼 Принял заявление: сотудник отдела {employee_first["department"]}, {employee_first["name"]} {employee_first["surname"]}\n'
        bot.send_message(chat_id=GENERIC_CHAT, text=message_text, message_thread_id=OTK_THREAD_ID)
        bot.send_message(message.from_user.id, 'Информация о проверке направлена в общий чат.', reply_markup=rmk)

        
            
    else:
        bot.send_warn(f'При попытке проверить личное дело абитуриента {bot.db.get_applicant_fullname_via_id(application_id=application_id)["applicant_fullname"]} у сотрудника отдела {employee["department"]},\nФИО: {employee["surname"]} {employee["name"]} произошла ошибка.\nОбратиться: {message.from_user.username}')
        bot.send_message(message.chat.id, '<b>Произошла неизвестная ошибка.</b>\nОбратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk) 
    

def find_applicant_start(message: Message, bot: TeleBot):
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('ФИО'), KeyboardButton('СНИЛС'))

    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Выберите тип поиска заявления.', reply_markup=rmk),
        find_applicant_get_type,
        bot=bot
    )


def find_applicant_get_type(message: Message, bot: TeleBot):
    ans = message.text

    if ans == 'ФИО':
        find_applicant_get_data_via_fullname(message=message, bot=bot)
    elif ans == 'СНИЛС':
        find_applicant_get_data_via_snils(message=message, bot=bot)
    else:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('ФИО'), KeyboardButton('СНИЛС'))

        bot.register_next_step_handler(
            bot.send_message(message.chat.id, 'Ошибка! Вы выбрали неверный тип поиска.\nВыберите тип поиска заявления.'),
            find_applicant_get_type,
            bot=bot
        )


def find_applicant_get_data_via_snils(message: Message, bot: TeleBot):
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите СНИЛС абитуриента.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00</code>'), 
        find_applicant, 
        find_by_snils = True, bot=bot
    )

def find_applicant_get_data_via_fullname(message: Message, bot: TeleBot):
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, 'Введите ФИО абитуриента.'), 
        find_applicant, 
        bot=bot
    )


def find_applicant(message: Message, bot: TeleBot, find_by_snils: bool = False):
    find_data = message.text
    
    if find_by_snils:
        find_data = find_data.replace('-', '').replace(' ', '')

        if (not find_data.isdigit()) or len(find_data) != 11:
            bot.register_next_step_handler(
                bot.send_message(message.chat.id, '❗️ <b>Ошибка!</b> Вы ввели неккоректный номер СНИЛС.\n<code>Укажите число из 11 знаков, в формате:\n16675209900\n166-752-099 00</code>'), 
                find_applicant,
                bot=bot, find_by_snils=find_by_snils
            )
            return
    else: 
        find_data = find_data.strip()

    applicators_list = bot.db.find_application_info(find_data = find_data, find_by_snils = find_by_snils)

    if len(applicators_list) == 0:
            rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            rmk.add(KeyboardButton('Список команд'), KeyboardButton('Найти заявление'))
            bot.send_message(message.chat.id, '❌ <b>Информация не найдена!</b>', reply_markup=rmk)
            return
    
    if len(applicators_list) > 20:
        rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        rmk.add(KeyboardButton('Список команд'), KeyboardButton('Найти заявление'))
        bot.send_message(message.chat.id, '❌ <b>Список подходящих заявлений слишком большой! Введите больше уточняющей информации.</b>', reply_markup=rmk)
        return

    answer = f'<b>Список подходящих заявок абитуриентов</b>'

    for i in applicators_list:
        answer += f'\n\n---\n\n<i>ФИО абитуриента:</i>\n 📍 {i["fullname"]}\n'
        
        if i['spo_number'] is not None:
            answer += f'<i>Номер СПО абитуриента:</i>\n 📍 {i["spo_number"]}\n'

        answer += f'<i>СНИЛС абитуриента:</i>\n 📍 {utils.snils_to_str(i["snils"]) if i["snils"] is not None else "Нет данных"}\n'
        answer += f'<i>Тип подачи документов:</i>\n 📍 {i["submit_method"]}\n'
        answer += f'<i>Статус заявления в ПК:</i>\n 📍 {"Принято" if i["status"] else "Отклонено"}\n'
        answer += f'<i>Наличие оригинала аттестата:</i>\n 📍  {"Сдан. 🟢" if i["passed_original_certificate"] else "Не сдан. 🔴"}'

        if not i['status']:
            answer += f'\n<i>Причина отклонениня заявления:</i>\n 📍 {i["deny_reason"]}' 

        answer += f'\n<i>Обработал:</i>\n 📍 {i["employee_fullname"]}'
        answer += f'\n<i>Дата обработки:</i>\n 📍 {datetime.fromtimestamp(i["datetime"]).strftime("%d.%m.%Y %H:%M") if i["datetime"] is not None else "Нет данных"}'
        answer += f'\n<i>Дело проверено отделом ОТК:</i>\n 📍 {"Да" if i["status_otk"] else "Нет"}'
        
        if i['status_otk']:
            answer += f'\n<i>Проверил сорудник ОТК:</i>\n 📍 {bot.db.get_employee_data(i["employee_otk_id"])["fullname"]}' # ФИ сотрудника ОТК 
            answer += f'\n<i>Ошибки в личном деле:</i>\n 📍 {"Найдены" if i["has_errors_otk"] else "Не найдены"}' 

            if i["has_errors_otk"]:
                answer += f'\n<i>Список ошибок:</i>\n 📍 {i["errors_otk"]}'

            answer += f'\n<i>Дата проверки:</i>\n 📍 {datetime.fromtimestamp(i["datetime_otk_check"]).strftime("%d.%m.%Y %H:%M") if i["datetime_otk_check"] is not None else "Нет данных"}'
            
                
            
                
    
    rmk = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rmk.add(KeyboardButton('Список команд'), KeyboardButton('Найти заявление'))
    
    bot.send_message(message.chat.id, answer, reply_markup=rmk)
        # bot.send_message(message.chat.id, '<b>❗️❗️❗️ Ответ на Ваш запрос слишком большой. Пожалуйста, введите более подробную информацию об абитуриенте.</b>\n\nЕсли ошибка возникает несколько раз подряд — обратитесь к разработчику бота <a href="https://t.me/iplexa">Алексею Шипилову</a>', reply_markup=rmk)
