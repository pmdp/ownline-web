import datetime
import uuid

from ownline_web import app
from ownline_web import db
from ownline_web.core.models import Service, UserService, Invitation
from flask import request, jsonify
from flask_jwt_extended import (jwt_required, current_user)

import re


########################################################################################################################
########################################################################################################################
# INVITATIONS

@app.route('/api/v1/invitations', methods=['GET'])
@jwt_required(fresh=True)
def get_all_user_invitations():
    active = request.args.get('active', default='true')
    response = []
    if active == 'true':
        invitations = db.session.query(Invitation).filter(Invitation.active == True).with_parent(current_user).all()

    else:
        invitations = db.session.query(Invitation).filter(Invitation.active == False).with_parent(current_user).all()
    for invitation in invitations:
        response.append(invitation.serialize())
    return jsonify({"invitations": response}), 200


@app.route('/api/v1/invitation/<invitation_id>', methods=['DELETE'])
@jwt_required(fresh=True)
def invitation_deletion(invitation_id):
    if not invitation_id or not re.compile(app.config['UUID_4_REGEX'], re.I).match(str(invitation_id)):
        return jsonify({"ok": False, "msg": "Invalid invitation"}), 400

    invitation = db.session.query(Invitation).filter(Invitation.public_id == invitation_id).with_parent(
        current_user).one_or_none()
    if invitation:
        db.session.delete(invitation)
        db.session.commit()
    else:
        app.logger.info(f"Error deleting invitation with id: {invitation_id}")
        return jsonify({"ok": False, "msg": "Error deleting invitation"}), 400

    return jsonify({"ok": True, "msg": "Invitation deleted"}), 200


@app.route('/api/v1/invitation', methods=['POST'])
@jwt_required(fresh=True)
def invitation_creation():
    if not request.is_json:
        return jsonify({'ok': False, "msg": "Invalid JSON"}), 400

    service_public_id = request.json.get('service_id')
    if not service_public_id or not re.compile(app.config['UUID_4_REGEX'], re.I).match(str(service_public_id)):
        return jsonify({"ok": False, "msg": "Invalid service_id"}), 400

    service = db.session.query(Service).join(UserService).filter(
        Service.public_id == service_public_id).filter(UserService.user_id == current_user.id).one_or_none()
    if not service:
        return jsonify({"ok": False, "msg": "Service doesnt not exist for current user"}), 400

    message = request.json.get('message')
    if message and len(message) > 254:
        return jsonify({"ok": False, "msg": "Invalid message length"}), 400

    duration = request.json.get('duration')
    if not duration:
        duration = app.config['DEFAULT_INVITATION_DURATION']
    if not isinstance(duration, int) or duration > app.config['MAX_INVITATION_DURATION']:
        return jsonify({"ok": False, "msg": "Invalid duration"}), 400

    invitation = Invitation(public_id=str(uuid.uuid4()),
                            sec_token=str(uuid.uuid4()),
                            service_id=service_public_id,
                            message=message,
                            duration=duration,
                            active=True,
                            end_timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=duration))
    current_user.invitations.append(invitation)
    db.session.commit()
    msg = f"*New invitation created*: user:_{current_user.username}_ |  message:{message} | service:{service.name} | druration:{duration}min"
    app.logger.info(msg)
    return jsonify({"ok": True, "msg": "Invitation created"}), 200



########################################################################################################################
########################################################################################################################

