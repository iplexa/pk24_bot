import re
import logging

from http.server import BaseHTTPRequestHandler
from urllib.parse import unquote

from telebot import TeleBot


class Bitrix24HTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, token: str, bot: TeleBot) -> None:
        self.token = token
        self.bot = bot
        super().__init__(request, client_address, server)

    def do_GET(self):
        self.send_response(403)
        self.send_header('Content-type', 'text/html;charset=utf-8')
        self.end_headers()

        logging.info(f'Пришёл GET-запрос от {self.client_address}. Код ответа: 403')
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        parsed_request_data = self.parse_bitrix24_request(request_string=unquote(body))

        if self.verify_bitrix24_request(parsed_request_data=parsed_request_data):
            self.send_response(200)

            if parsed_request_data.get('event') is not None:
                event_name = parsed_request_data['event']
                self.bot.bitrix24.request_handler(event_name=event_name, event_data=parsed_request_data)
        
            logging.info(f'Пришёл POST-запрос от Битрикс24. Код ответа: 200')
        else:
            self.send_response(403)
            logging.info(f'Пришёл POST-запрос от {self.client_address}. Код ответа: 403')
        
        self.send_header('Content-type', 'text/html;charset=utf-8')
        self.end_headers()

    def parse_bitrix24_request(self, request_string):
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
