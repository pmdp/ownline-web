import http.client
import urllib.parse
from .cmd import execute_command


class NotifyService(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.notify_services = []

        # Append telegram service
        if app.config['TELEGRAM_BOT_API_KEY'] and app.config['TELEGRAM_CHAT_ID']:
            self.notify_services.append(TelegramNotifyService(bot_api_key=app.config['TELEGRAM_BOT_API_KEY'],
                                                              chat_id=app.config['TELEGRAM_CHAT_ID']))

        # Append system log service
        if app.config['SYSLOG_LOGGER_PATH']:
            self.notify_services.append(SystemLogNotifyService(app.config['SYSLOG_LOGGER_PATH']))

        if len(self.notify_services) == 0:
            app.logger.warn("No notify services set")

    def notify_all(self, message):
        for notify_service in self.notify_services:
            notify_service.notify(message)


class TelegramNotifyService(object):

    API_ENDPOINT = 'api.telegram.org'

    SEND_MESSAGE_URL = '/bot{{bot_api_key}}/sendMessage?'

    def __init__(self, bot_api_key=None, chat_id=None):
        self.timeout = 6
        self.bot_api_key = bot_api_key
        self.chat_id = chat_id

    def notify(self, message):
        # todo: make static method?
        # curl -X GET https://api.telegram.org/bot<apikey>/sendMessage?chat_id=<chatId>&text=<someText>
        try:
            connection = http.client.HTTPSConnection(self.API_ENDPOINT, timeout=self.timeout)
            encoded_payload = urllib.parse.urlencode({'chat_id': self.chat_id,
                                                      'text': message,
                                                      'parse_mode': 'Markdown'})
            url = self.SEND_MESSAGE_URL.replace('{{bot_api_key}}', self.bot_api_key) + encoded_payload
            connection.request('GET', url)
            response = connection.getresponse()
            # response.read().decode('utf-8').strip()
            if response.status:
                return True
            else:
                raise Exception("Telegram request status: ".format(response.status))
        except Exception as e:
            return False


class SystemLogNotifyService(object):

    def __init__(self, logger_path):
        self.logger_path = logger_path

    def notify(self, message):
        status, stderr, stdout = execute_command([self.logger_path, '-t', 'ownline',  '-p', 'INFO', message])

        if status:
            return True
        else:
            return False

