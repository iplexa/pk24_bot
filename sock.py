import functools as ft

from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from telebot import TeleBot

import utils

from constants import GENERIC_CHAT, CALL_THREAD_ID


class Bitrix24HTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, token: str, bot: TeleBot) -> None:
        self.token = token
        self.bot = bot
        super().__init__(request, client_address, server)

    def do_GET(self):
        self.send_response(403)
        self.send_header('Content-type', 'text/html;charset=utf-8')
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        parsed_request_data = self.parse_bitrix24_request(request_string=unquote(body))

        if self.verify_bitrix24_request(parsed_request_data=parsed_request_data):
            self.send_response(200)

            if parsed_request_data.get('event') is not None:
                event_name = parsed_request_data['event']

                print(parsed_request_data)

                match event_name:
                    case 'ONVOXIMPLANTCALLSTART':
                        employee = self.bot.db.get_employee_via_bitrix_id(bitrix_id = (parsed_request_data["data"]["USER_ID"]))
                        datetime_int = datetime.now().timestamp()
                        
                        if not self.bot.db.send_call_on_start(employee_id_start = employee['id'], call_id = parsed_request_data['data']['CALL_ID'], datetime_int = datetime_int):
                            self.bot.db.send_warn(f'<b>CallCentre: при попытке записи в базу звонка с id {parsed_request_data["data"]["CALL_ID"]}, который совершается сотрудником {employee["fullname"]} произошла ошибка!</b>')

                    case 'ONCRMLEADADD':
                        self.bot.send_message(chat_id=GENERIC_CHAT, message_thread_id=CALL_THREAD_ID, text=f'Был создан новый лид c ID {parsed_request_data["data"]["FIELDS"]} в Битрикс24\nПришёл запрос от Битрикс24: {unquote(body)}')
        
                    case 'ONVOXIMPLANTCALLEND':
                        employee_end_call = self.bot.db.get_employee_via_bitrix_id(parsed_request_data["data"]["PORTAL_USER_ID"])
                        employee_start_call_id = self.bot.db.send_call_on_end(call_id = parsed_request_data['data']['CALL_ID'], employee_id_end = employee_end_call['id'], phone_number = int(parsed_request_data['data']['PHONE_NUMBER']), call_duration = int(parsed_request_data['data']['CALL_DURATION']))

                        if employee_start_call_id:
                            employee_start_call = self.bot.db.get_employee_data(employee_start_call_id['employee_id_start'])                          

                            message_text = f'Сотрудник <b>{employee_start_call["name"]} {employee_start_call["surname"]}</b> обработал вызов в Битрикс24.\n'
                            message_text += f'Номер телефона: {parsed_request_data["data"]["PHONE_NUMBER"]}\n'
                            message_text += f'Время разговора: {utils.seconds_to_simple_time_str(int(parsed_request_data["data"]["CALL_DURATION"]), seconds_needed=True)}\n'
                            if employee_start_call_id['employee_id_start'] != employee_end_call['id']:
                                message_text += f'Вызов был перенаправлен на сотрудника отдела {employee_end_call["department"]}, {employee_end_call["fullname"]}.'
                            self.bot.send_message(chat_id=GENERIC_CHAT, message_thread_id=CALL_THREAD_ID, text=message_text)
        else:
            self.send_response(403)
        
        self.send_header('Content-type', 'text/html;charset=utf-8')
        self.end_headers()

    def parse_bitrix24_request(self, request_string):
        import re

        pattern = r'([^=]+)=([^&]+)'
        matches = re.findall(pattern, request_string)
        request_dict = {}

        for key, value in matches:
            key = key.replace('&', '')  # Убираем символ &
            
            if '[' in key:
                main_key, sub_key = re.match(r'([^[]+)\[([^\]]+)\]', key).groups()

                if main_key not in request_dict:
                    request_dict[main_key] = {}
                request_dict[main_key][sub_key] = value
            else:
                request_dict[key] = value
        
        return request_dict

    def verify_bitrix24_request(self, parsed_request_data: dict) -> bool:
        if parsed_request_data.get('auth', {}).get('application_token', None) is None:
            return False
        else:
            if parsed_request_data['auth']['application_token'] != self.token:
                return False
            else:
                return True


class Bitrix24API:
    def __init__(self, bot: TeleBot):
        self.http_request_handler = Bitrix24HTTPRequestHandler
        self.token = '7ll06vec9w0olfndnu6xbb0wg7cpeoyp'
        self.bot = bot
    
    def create_request_handler_object(self, *args, **kwargs) -> Bitrix24HTTPRequestHandler:
        return Bitrix24HTTPRequestHandler(*args, **kwargs)

    def start_listen_outgoing_webhooks(self, host: str, port: int) -> None:
        httpd = HTTPServer(
            server_address=(host, port),
            RequestHandlerClass=ft.partial(self.create_request_handler_object, token=self.token, bot=self.bot)
        ) 
        httpd.serve_forever()
