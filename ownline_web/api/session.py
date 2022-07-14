from ownline_web import app, ownline
from ownline_web import db, notify_service
from ownline_web.core.models import Service, Session, UserService
from flask import request, jsonify
from flask_jwt_extended import (jwt_required, current_user)
import re
import datetime

# SESSION
########################################################################################################################
########################################################################################################################
# SESSIONS
from ownline_web.utils.remote_addr import get_remote_addr


@app.route('/api/v1/session', methods=['GET'])
@jwt_required(fresh=True)
def get_all_user_sessions():
    # todo: pagination: http://flask-sqlalchemy.pocoo.org/2.3/api/#flask_sqlalchemy.BaseQuery.paginate
    # todo: serialize all sessions at once https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
    active = request.args.get('active', default='true')
    if active == 'true':
        result = db.session.query(Session)\
            .join(Session.service)\
            .filter(Session.user == current_user)\
            .filter(Session.terminated == False)\
            .order_by(Session.date_modified.desc()).all()
    else:
        # todo: pageable finished sessions, remove limit
        result = db.session.query(Session)\
            .join(Session.service)\
            .filter(Session.user == current_user)\
            .filter(Session.terminated == True)\
            .order_by(Session.date_modified.desc()).limit(100)
    response = []
    for obj in result:
        response.append(obj.serialize())
    return jsonify({"sessions": response}), 200


@app.route('/api/v1/session', methods=['POST'])
@jwt_required(fresh=True)
def session_request():
    if not request.is_json:
        return jsonify({'ok': False, "msg": "Invalid JSON"}), 400

    service_public_id = request.json.get('service_id')

    if not service_public_id or not re.compile(app.config['UUID_4_REGEX'], re.I).match(str(service_public_id)):
        return jsonify({"ok": False, "msg": "Invalid service_id"}), 400

    # service = Service.query.filter_by(public_id=service_public_id).one_or_none()
    query_result = db.session.query(Service, UserService.port_dst).join(UserService).filter(
        Service.public_id == service_public_id).filter(UserService.user_id == current_user.id).one_or_none()
    if not query_result or len(query_result) != 2:
        return jsonify({"ok": False, "msg": "Error getting service"}), 400

    service = query_result[0]
    port_dst = query_result[1]
    duration = int(request.json.get('duration', 0))
    trusted_ip = get_remote_addr(request)

    result = add_session(duration, port_dst, service, trusted_ip)
    if result:
        return jsonify({"ok": True}), 200
    else:
        app.logger.error("Error creating session")
        return jsonify({"ok": False, "msg": "FAIL"}), 400


def add_session(duration, port_dst, service, trusted_ip):
    # Call ownline to add a the new session
    result = ownline.do_add(trusted_ip, service, port_dst, duration)
    if result:
        # Save new session at db
        session = Session(public_id=result['session_public_id'],
                          service_id=service.id,
                          port_dst=result['port_dst'],
                          duration=result['duration'],
                          end_timestamp=datetime.datetime.utcfromtimestamp(result['end_timestamp']),
                          trusted_ip=result['trusted_ip'])
        current_user.sessions.append(session)
        db.session.commit()
        msg = f"*New session created*: _{current_user.username}_ -> {service.name} by {result['trusted_ip']} for {result['duration']} min"
        app.logger.info(msg)
        notify_service.notify_all(msg)
        return True
    else:
        app.logger.error("Error creating session")
        return False


@app.route('/api/v1/session/<session_id>', methods=['DELETE'])
@jwt_required(fresh=True)
def delete_session(session_id):
    if not session_id or not re.compile(app.config['UUID_4_REGEX'], re.I).match(str(session_id)):
        return jsonify({"ok": False, "msg": "Invalid session_id"}), 400

    session = Session.query.filter_by(public_id=session_id).one_or_none()
    if not session:
        return jsonify({"ok": False, "msg": "non-existent requested session"}), 400

    app.logger.debug(f"Terminating session: {session_id}")

    result = ownline.do_del(session)
    if result:
        session.terminated = True
        db.session.commit()
        msg = f"*Session terminated* for _{current_user.username}_ from {session.trusted_ip} to _{session.service.name}_"
        app.logger.info(msg)
        notify_service.notify_all(msg)
        return jsonify({"ok": True}), 200
    else:
        return jsonify({"ok": False, "msg": "FAIL"}), 400


@app.route('/api/v1/flush', methods=['POST'])
@jwt_required(fresh=True)
def flush_all_sessions():
    app.logger.info("Flushing all sessions")
    # todo: only apply this for user sessions, not all rules
    sessions = Session.query.with_parent(current_user).filter(Session.terminated == False).all()
    if len(sessions) > 0:
        for session in sessions:
            if ownline.do_del(session):
                session.terminated = True
                msg = f"*Session flushed*: {session.user.username} -> {session.service.name} from {session.trusted_ip}"
                app.logger.info(msg)
                notify_service.notify_all(msg)
        db.session.commit()
    return jsonify({"ok": True, "msg": "OK"}), 200


@app.route('/api/v1/session/check_expired', methods=['POST'])
def check_expired():
    sessions = Session.query.filter(Session.terminated == False) \
        .filter(Session.end_timestamp < datetime.datetime.utcnow()).all()
    if len(sessions) > 0:
        for session in sessions:
            if ownline.do_del(session):
                session.terminated = True
                msg = f"*Session expired*: {session.user.username} -> {session.service.name} from {session.trusted_ip}"
                app.logger.info(msg)
                notify_service.notify_all(msg)
        db.session.commit()
    return jsonify({"ok": True, "msg": "OK"}), 200


########################################################################################################################
########################################################################################################################




