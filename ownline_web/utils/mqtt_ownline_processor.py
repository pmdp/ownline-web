from ownline_web import app, ownline
from ownline_web import db
from ownline_web.api.session import add_session
from ownline_web.core.models import Invitation
from flask_jwt_extended import (current_user)
import re
import hashlib
import hmac
import json

from ownline_web.utils.update_user_automatic_services import update_user_automatic_services


def process_mqtt_invitation_message(payload):
    """
    Invitation trigger

    """
    app.logger.debug(f"Processing MQTT invitation message: {payload}")
    if 'token' not in payload.keys() or not re.compile(app.config['UUID_4_REGEX']).match(payload['token']):
        app.logger.error("Invalid or null token")
        return
    if 'trusted_ip' not in payload.keys() or not re.compile(app.config['IP_V4_REGEX']).match(payload['trusted_ip']):
        app.logger.error(f"Invalid MQTT message trusted_ip: '{payload['trusted_ip']}'")
        return

    invitation = db.session.query(Invitation).filter(
        Invitation.sec_token == payload['token']).with_parent(current_user).one_or_none()
    if not invitation:
        app.logger.error(f"No invitation with that token: '{payload['token']}'")
        return

    port_dst = ownline.get_free_random_port()
    result = add_session(invitation.duration, port_dst, invitation.service, payload['trusted_ip'])
    if result:
        app.logger.info(f"New invitation session created")
    else:
        app.logger.error(f"Error creating invitation session: '{invitation}'")


def process_mqtt_new_ip_message(payload):
    """ This method is executed when a message comes from MQTT new_ip topic with a user id and IP
        Also checks for a valid signature created with the pair (user_id, ip)

        So when a new ip comes, automatically a session will be created for every user automatic service.
        If there is already a session created for a service, update its end_timestamp if less than 1/5 of duration

    """
    app.logger.debug(f"Processing MQTT new_ip message: {payload}")
    if 'msg' not in payload.keys() or 'signature' not in payload.keys():
        app.logger.error("Invalid payload, does not contain signature or message")
        return
    # payload structure and content validation
    if 'trusted_ip' not in payload['msg'].keys() or not re.compile(app.config['IP_V4_REGEX']).match(
            payload['msg']['trusted_ip']):
        app.logger.error(f"Invalid MQTT message trusted_ip: '{payload['msg']['trusted_ip']}'")
        return
    if 'user_id' not in payload['msg'].keys() or not re.compile(app.config['UUID_4_REGEX']).match(
            payload['msg']['user_id']):
        app.logger.error(f"Invalid MQTT message user_id: '{payload['msg']['user_id']}'")
        return

    # Check for valid signature
    signed_msg = json.dumps(payload['msg'], separators=(',', ':')).encode('utf-8')
    actual_signature = hmac.new(app.config.get('HMAC_KEY'), signed_msg, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(payload['signature'], actual_signature):
        app.logger.error("Invalid message signature")
        return

    update_user_automatic_services({'trusted_ip': payload['msg']['trusted_ip'],
                                    'user_id': payload['msg']['user_id']})

