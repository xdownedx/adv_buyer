import logging
import requests

class TelegramLoggingHandler(logging.Handler):
    def __init__(self, telegram_bot_token, telegram_chat_id):
        super().__init__()
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

    def emit(self, record):
        log_entry = self.format(record)
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': log_entry,
            'disable_notification': True
        }
        requests.post(f'https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage', data=payload)
