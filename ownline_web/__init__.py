from flask import Flask
from .config import config
from flask_mqtt import Mqtt
from flask.helpers import get_env

app = Flask(__name__, static_folder=None)

# Loads configuration by environment
env = get_env()

# Initialize flask app configuration
app.config.from_object(config[env])
config[env].init_app(app)

app.logger.info("Environment: {}".format(env))
app.logger.info("Init app config finished")

from werkzeug.middleware.proxy_fix import ProxyFix
# App is behind one proxy that sets the -For and -Host headers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
app.logger.info("Init proxy fix finished")

# Initialize flask-jwt-extended extension
from flask_jwt_extended import JWTManager
jwt = JWTManager(app)
app.logger.info("Init jwt extension finished")

# Initialize Flask-SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
app.logger.info("Init SQLAlchemy extension finished")

# Notify service
from .utils.notify_service import NotifyService
notify_service = NotifyService(app)
app.logger.info("Init NotifyService finished")

# Intialize ownline extension
from .core.ownline_action import OwnlineAction
ownline = OwnlineAction(app)

# from flask_migrate import Migrate
# migrate = Migrate(app, db)

# Intialize Flask-CORS
from flask_cors import CORS
if env == 'production':
    allowed_origins = [app.config['HOST_NAME'], ]
else:
    allowed_origins = ["*", ]
cors = CORS(app, origins=allowed_origins, methods=['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'DELETE'])

from .core import models
from .api import connections, invitations, misc, service, session
from .auth import auth

# Must be after api import to work
if app.config['MQTT_SERVICE_ACTIVE']:
    mqtt = Mqtt(app)
    from .utils import mqtt_subscriber
    app.logger.info("Init MQTT finished")


# # todo: Remove this for production, only normal static routing (with nginx X-Accel)
# if app.config['FLASK_DEBUG']:
#     from .auth import dev_static_serve
# else:
#     from .auth import static_routing


# @app.errorhandler(Exception)
# def unhandled_exception(e):
#     app.logger.exception("Unhandled Exception", e)
#     return '', 500


# @app.cli.command()
# def initdb():
#     """Initialize the database."""
#     db.drop_all()
#     db.create_all()
#     click.echo('DB initializated')


# @app.cli.command()
# def initialize():
#     app.logger.info("Initializing as first boot or reboot")
#     from .core.initialize import initialize
#     initialize()


app.logger.info("Finish app init")
