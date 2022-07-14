import os
import datetime
import logging
from logging.config import dictConfig

basedir = os.path.abspath(os.path.dirname(__package__))


def get_env_or_def(env_name, default_value):
    # Return env_value if exists or default_value
    env_value = os.environ.get(env_name)
    return env_value if env_value else default_value


class Config(object):
    # Flask general
    FLASK_DEBUG = False
    TESTING = False
    LOGGER_NAME = "ownline_web_logger"
    LOGGING_LEVEL = logging.DEBUG

    ADMIN_USER_ID = int(get_env_or_def('OWNLINE_ADMIN_USER_ID', 1))

    HOST_NAME = get_env_or_def('OWNLINE_HOST_NAME', 'ownline.localhost')
    BASE_HOST_NAME = get_env_or_def('OWNLINE_BASE_HOST_NAME', 'localhost')
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'very-secret-thing'  # use binascii.hexlify(os.urandom(24))
    HMAC_KEY = get_env_or_def('OWNLINE_HMAC_KEY', '123').encode()

    # ownline-core CMD server
    CMD_SERVER_IP = get_env_or_def('OWNLINE_CMD_SERVER_IP', '127.0.0.1')
    CMD_SERVER_PORT = int(get_env_or_def('OWNLINE_CMD_SERVER_PORT', 57329))
    CMD_SERVER_CERT_PATH = get_env_or_def('OWNLINE_CMD_SERVER_CERT_PATH', os.path.join(basedir, 'selfsigned.cert'))
    CMD_SERVER_KEY_PATH = get_env_or_def('OWNLINE_CMD_SERVER_KEY_PATH', os.path.join(basedir, 'selfsigned.key'))
    CMD_SERVER_CERT_PASSWORD = get_env_or_def('OWNLINE_CMD_SERVER_CERT_PASSWORD', 'Password1')

    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_BAN_HOURS = 1

    # Default session duration
    DEFAULT_SESSION_DURATION = int(get_env_or_def('OWNLINE_DEFAULT_SESSION_DURATION', 3))

    # Max session duration (default 24h)
    MAX_SESSION_DURATION = int(get_env_or_def('OWNLINE_MAX_SESSION_DURATION', 1440))

    # Default invitation duration
    DEFAULT_INVITATION_DURATION = int(get_env_or_def('OWNLINE_DEFAULT_INVITATION_DURATION', 3))
    
    # Max invitation duration (default 24h)
    MAX_INVITATION_DURATION = int(get_env_or_def('OWNLINE_MAX_INVITATION_DURATION', 1440))

    INVITATION_URL = get_env_or_def('OWNLINE_INVITATION_URL', 'https://invitation.example.org?token=')

    # LAN network CIDR IP, for local access and security validations
    LAN_NETWORK = get_env_or_def('OWNLINE_LAN_NETWORK', '192.168.1.0/24')

    # SQLALchemy database ORM
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, 'db-test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AUTOMATIC_SESSION_DURATION = int(get_env_or_def('OWNLINE_AUTOMATIC_SESSION_DURATION', 5))
    MAX_SPA_DIFF_TS = int(get_env_or_def('OWNLINE_MAX_SPA_DIFF_TS_MINUTES', 1))*60*1000

    USERNAME_REGEX = '^(?=.{3,20}$)(?![_.])(?!.*[_.]{2})[a-zA-Z0-9._]+(?<![_.])$'
    PASSWORD_REGEX = '^(?=.*[a-z])(?=.*[A-Z])(?=.*÷\\d)[a-zA-Z\\d]{8,}$'
    UUID_4_REGEX = '[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}'
    IP_V4_REGEX = '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/32|)$'
    IP_V4_REGEX_CIDR = '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{2}$'
    TIMESTAMP_REGEX = '^\d{13}$'
    MAX_TCP_PORT = 65535

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret'
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES')) \
        if os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_MINUTES') else 15
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=os.environ.get('JWT_ACCESS_TOKEN_TIME_DELTA')) \
        if os.environ.get('JWT_ACCESS_TOKEN_TIME_DELTA') else datetime.timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(minutes=os.environ.get('JWT_REFRESH_TOKEN_TIME_DELTA')) \
        if os.environ.get('JWT_REFRESH_TOKEN_TIME_DELTA') else datetime.timedelta(days=40)
    JWT_TOKEN_LOCATION = ['headers', 'cookies'] # ['headers', 'cookies', 'json']
    JWT_ALGORITHM = 'HS512'
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = ''
    JWT_ACCESS_COOKIE_PATH = '/api/'
    JWT_ACCESS_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'

    # MQTT
    MQTT_SERVICE_ACTIVE = bool(os.environ.get('OWNLINE_WEB_MQTT_SERVICE_ACTIVE')) if (os.environ.get('OWNLINE_WEB_MQTT_SERVICE_ACTIVE') and int(os.environ.get('OWNLINE_WEB_MQTT_SERVICE_ACTIVE')) > 0) else False # active/disable mqtt
    MQTT_BROKER_URL = os.environ.get('OWNLINE_WEB_MQTT_BROKER_URL')
    MQTT_BROKER_PORT = int(os.environ.get('OWNLINE_WEB_MQTT_BROKER_PORT')) if os.environ.get('OWNLINE_WEB_MQTT_BROKER_PORT') else 1883
    MQTT_USERNAME = os.environ.get('OWNLINE_WEB_MQTT_USERNAME') or 'user'
    MQTT_PASSWORD = os.environ.get('OWNLINE_WEB_MQTT_PASSWORD') or 'password'
    MQTT_KEEPALIVE = int(os.environ.get('OWNLINE_WEB_MQTT_KEEPALIVE')) if os.environ.get('OWNLINE_WEB_MQTT_KEEPALIVE') else 10
    MQTT_TOPIC_NEW_USER_IP = os.environ.get('OWNLINE_WEB_MQTT_TOPIC_NEW_USER_IP') or '/ip_update'
    MQTT_TOPIC_INVITATION = os.environ.get('OWNLINE_WEB_MQTT_TOPIC_INVITATION') or '/invitation'
    MQTT_TLS_ENABLED = bool(os.environ.get('OWNLINE_WEB_MQTT_TLS_ENABLED')) if os.environ.get('OWNLINE_WEB_MQTT_TLS_ENABLED') else False
    # # todo: get not expired cloudmqtt cert
    # MQTT_TLS_CERT_REQS = ssl.CERT_NONE
    #MQTT_TLS_INSECURE = bool(os.environ.get('OWNLINE_WEB_MQTT_TLS_INSECURE')) if os.environ.get('OWNLINE_WEB_MQTT_TLS_INSECURE') else False
    MQTT_TLS_CA_CERTS = os.environ.get('OWNLINE_WEB_MQTT_TLS_CA_CERTS') or None

    # Notify services
    SYSLOG_LOGGER_PATH = get_env_or_def('SYSLOG_LOGGER_PATH', False)
    TELEGRAM_BOT_API_KEY = os.environ.get('TELEGRAM_BOT_API_KEY') or False
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID') or False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    FLASK_DEBUG = True
    SQLALCHEMY_ECHO = True

    # JWT
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False


class TestingConfig(Config):
    TESTING = True
    SSL_CHECK_HOSTNAME = False


class ProductionConfig(Config):
    LOGGING_LEVEL = logging.INFO
    LOGGING_FILE = os.environ.get('OWNLINE_LOG_FILE') or 'ownline_web.log'

    # JWT
    # JWT_COOKIE_SECURE = True  # todo: should be activated
    JWT_COOKIE_CSRF_PROTECT = False  # do the double cookie set # todo: should be activated

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # log to file
        # import logging
        # app.logg
        # logging.basicConfig(level=app.config['LOGGING_LEVEL'],
        #                     format='%(levelname)s - %(threadName)s - %(asctime)s - %(module)s: %(message)s',
        #                     filename=app.config['LOGGING_FILE'])

        # file_handler = logging.FileHandler(app.config['LOGGING_FILE'])
        # file_handler.setLevel(app.config['LOGGING_LEVEL'])
        # file_handler.setFormatter(logging.Formatter('%(levelname)s - %(asctime)s - %(module)s: %(message)s'))
        # app.logger.handlers = []
        # app.logger.addHandler(file_handler)
        # app.logger.setLevel(app.config['LOGGING_LEVEL'])


class GunicornConfig(ProductionConfig):

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)


class DockerConfig(ProductionConfig):

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        dictConfig({
            'version': 1,
            'formatters': {'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
            }},
            'handlers': {'wsgi': {
                'class': 'logging.StreamHandler',
                'formatter': 'default'
            }},
            'root': {
                'level': 'INFO',
                'handlers': ['wsgi']
            }
        })


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'gunicorn': GunicornConfig,
    'default': DevelopmentConfig
}
