import logging
import functools as ft
import requests

from datetime import datetime
from http.server import HTTPServer

from telebot import TeleBot

from .request_handler import Bitrix24HTTPRequestHandler
from utils import phone_number_to_str, seconds_to_simple_time_str
from constants import BITRIX24_WEBHOOK_TOKEN, GENERIC_CHAT, CALL_THREAD_ID


class Bitrix24API:
    def __init__(self, bot: TeleBot):
        self._http_request_handler = Bitrix24HTTPRequestHandler
        self.token = BITRIX24_WEBHOOK_TOKEN
        self.bot = bot
    
    def request_handler(self, event_name: str, event_data: dict):
        match event_name:
            case 'ONVOXIMPLANTCALLSTART':
                self.start_call_handler(event_data=event_data)
            
            case 'ONVOXIMPLANTCALLEND':
                self.end_call_handler(event_data=event_data)

            case 'ONCRMLEADADD':
                pass
                
            case _:
                pass

    def start_call_handler(self, event_data: dict):
        employee = self.bot.db.get_employee_via_bitrix_id(bitrix_id=event_data['data']['USER_ID'])

        if employee is not None:
            if not self.bot.db.send_call_on_start(call_id=event_data['data']['CALL_ID'], employee_id_start=employee['id']):
                self.bot.send_warn(f'<b>CallCentre: при попытке записи в базу звонка с ID {event_data["data"]["CALL_ID"]}, который совершается сотрудником {employee["employee_fullname"]}, произошла ошибка!</b>')
        
    def end_call_handler(self, event_data: dict):
        employee_start_call = self.bot.db.get_employee_via_call_id(call_id=event_data['data']['CALL_ID'])
        employee_end_call = self.bot.db.get_employee_via_bitrix_id(bitrix_id=event_data['data']['PORTAL_USER_ID'])
        if employee_start_call is None or employee_end_call is None:
            return
        phone_number = int(event_data['data']['PHONE_NUMBER'])
        call_duration = int(event_data['data']['CALL_DURATION'])
        call_duration_min, call_duration_sec = divmod(call_duration, 60)
        call_start_date = datetime.fromisoformat(event_data['data']['CALL_START_DATE'])

        message = f'📞 Сотрудник <b>{employee_start_call["employee_fullname"]}</b> обработал вызов в Битрикс24.\n'

        if employee_end_call is not None:
            # Обновляем информациб в базе о заверщении вызова
            self.bot.db.send_call_on_end(
                call_id=event_data['data']['CALL_ID'],
                employee_id_end=employee_end_call['id'],
                phone_number=phone_number,
                call_duration=call_duration,
                call_start_date=call_start_date.timestamp()
            )

            if employee_start_call['id'] != employee_end_call['id']:
                message += f'➡️ Вызов был перенаправлен на сотрудника <b>{employee_end_call["employee_fullname"]}</b> из отдела <b>{employee_end_call["department"]}</b>.\n'
        else:
            message += f'➡️ Вызов был перенаправлен на сотрудника [ID: {event_data["data"]["PORTAL_USER_ID"]}, не являющегося сотрудником Приёмной комиссии КМПО РАНХиГС 2024.\n'
        
        message += f'📱 Номер абонента:\n{phone_number_to_str(phone_number)}\n'
        message += '⏱ Длительность вызова:\n%02d:%02d сек.\n' % (call_duration_min, call_duration_sec)
        message += f'📅 Дата и время вызова:\n{call_start_date.strftime("%d.%m.%Y %H:%M:%S")}\n'

        call_data = self.get_call_data(call_id=event_data['data']['CALL_ID'])

        if call_data is not None:
            self.bot.send_audio(
                chat_id=GENERIC_CHAT,
                message_thread_id=CALL_THREAD_ID,
                caption=message,
                audio=call_data['CALL_RECORD_URL'],
                duration=call_data['CALL_DURATION']
            )
        else:
            message += f'⏺ Запись вызова: Нет данных'
            self.bot.send_message(chat_id=GENERIC_CHAT, message_thread_id=CALL_THREAD_ID, text=message)

    def get_call_data(self, call_id: str):
        response = requests.get(url=f'https://ranepa.bitrix24.ru/rest/3088/97ri5ejmsftjci31/voximplant.statistic.get.json?FILTER[CALL_ID]={call_id}')

        if response.status_code == 200:
            response = response.json()
            
            if len(response['result']) != 0:
                return response['result'][0]
            else:
                logging.warning(f'Не найдена запись звонка в Битрикс24 с ID: {call_id}')
                return None
        else:
            logging.warning(f'Отправленный запрос [get_call_data: call_id={call_id}] в Битрикс24 завершился неудачно. Код ответа: {response.status_code}')
            return None

    def create_request_handler_object(self, *args, **kwargs) -> Bitrix24HTTPRequestHandler:
        return Bitrix24HTTPRequestHandler(*args, **kwargs)

    def start_listen_outgoing_webhooks(self, host: str, port: int) -> None:
        httpd = HTTPServer(
            server_address=(host, port),
            RequestHandlerClass=ft.partial(self.create_request_handler_object, token=self.token, bot=self.bot)
        ) 
        httpd.serve_forever()