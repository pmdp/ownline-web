from ownline_web import app
from ownline_web import mqtt
import json
from flask_mqtt import MQTT_LOG_ERR, MQTT_LOG_INFO

from ownline_web.utils.mqtt_ownline_processor import process_mqtt_new_ip_message, process_mqtt_invitation_message


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    app.logger.info(f"Subscribing to : {app.config['MQTT_TOPIC_NEW_USER_IP']}")
    mqtt.subscribe(app.config['MQTT_TOPIC_NEW_USER_IP'])

    app.logger.info(f"Subscribing to : {app.config['MQTT_TOPIC_INVITATION']}")
    mqtt.subscribe(app.config['MQTT_TOPIC_INVITATION'])



@mqtt.on_disconnect()
def handle_disconnect():
    app.logger.info(f"Disconected from MQTT broker")


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    app.logger.info(f"New MQTT message arrives: {message.payload}")
    try:
        if message.topic == app.config['MQTT_TOPIC_NEW_USER_IP']:
            payload = json.loads(message.payload)
            process_mqtt_new_ip_message(payload)
        elif message.topic == app.config['MQTT_TOPIC_INVITATION']:
            payload = json.loads(message.payload)
            process_mqtt_invitation_message(payload)
        else:
            app.logger.warn("Incoming MQTT message to unknown topic: {}", message.topic)
    except ValueError as e:
        app.logger.error("{}: {}".format(type(e).__name__, e))

    except Exception as e:
        app.logger.error("{}: {}".format(type(e).__name__, e))


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    if level == MQTT_LOG_ERR:
        app.logger.error(buf)
    elif level == MQTT_LOG_INFO:
        app.logger.info(buf)
    else:
        app.logger.debug(buf)

# def is_connected():
#     return mqtt.connected
