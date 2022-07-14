from ownline_web import app, ownline
from ownline_web import db, notify_service
from ownline_web.core.models import Service, Session, UserService
from flask import request, jsonify
from flask_jwt_extended import (jwt_required, current_user)
import re
import time

from ownline_web.utils.remote_addr import get_remote_addr
from ownline_web.utils.update_user_automatic_services import update_user_automatic_services


########################################################################################################################
########################################################################################################################


@app.route('/api/v1/new_ip', methods=['POST'])
@jwt_required(refresh=True)
def new_ip_token_message():
    if not request.is_json:
        return jsonify({'ok': False, "msg": "Invalid JSON"}), 400

    trusted_ip = request.json.get('trusted_ip')
    if trusted_ip is None or not re.compile(app.config['IP_V4_REGEX']).match(trusted_ip):
        app.logger.error(f"Invalid new IP message trusted_ip: '{trusted_ip}'")
        return jsonify({'ok': False, "msg": "Invalid trusted_ip"}), 400

    update_user_automatic_services({'trusted_ip': trusted_ip,
                                    'user_id': current_user.public_id})
    return jsonify({"ok": True}), 200


########################################################################################################################
########################################################################################################################

@app.route('/api/v1/public_ip', methods=['GET'])
@jwt_required(fresh=True)
def get_public_ip():
    # remote_addr = get_remote_addr(request)
    # app.logger.info(request.headers)
    # app.logger.info("get_remote_addr(request): {}".format(get_remote_addr(request)))
    # app.logger.info("environ X-Real-IP: {}".format(request.environ.get('X-Real-IP')))
    # app.logger.info("environ X-Forwarded-For: {}".format(request.environ.get('X-Forwarded-For')))
    return jsonify(
        {"public_ip": get_remote_addr(request) + '/32'})  # or access_route[0] for get HTTP_X_FORWARDED_FOR nginx proxy


########################################################################################################################
########################################################################################################################

@app.route('/api/v1/ownline-web/ping', methods=['GET'])
def ping_ownline_web():
    app.logger.debug("Pinging ownline web service")
    current_time = round(time.time() * 1000)
    app.logger.debug("Response: current time: {}".format(current_time))
    if current_time:
        return jsonify({'ok': True, 'time': current_time}), 200
    else:
        return jsonify({"ok": False, "msg": "FAIL"}), 400


########################################################################################################################
########################################################################################################################


@app.route('/api/v1/ownline-core/ping', methods=['GET'])
@jwt_required(fresh=True)
def ping_ownline_core():
    app.logger.debug("Pinging ownline web service")
    start = time.time()
    result = ownline.ping()
    end = time.time()
    total = round((end - start) * 1000)
    if result["ok"]:
        return jsonify({'ok': True, 'time': total}), 200
    else:
        return jsonify({"ok": False, "msg": "FAIL"}), 400


########################################################################################################################
########################################################################################################################

@jwt_required(refresh=True)
@app.route('/api/v1/initialize', methods=['POST'])
def initialize():
    app.logger.info("Initializing ownline rules and sessions")
    notify_service.notify_all("Initializing ownline rules and sessions")
    # Intialize all actioners (clean iptables chains, rules and nginx files)
    ownline.initialize()

    # Generate LAN access to ownline
    query_result = db.session.query(Service, UserService.port_dst).join(UserService).filter(
        Service.name == 'ownline').filter(UserService.user_id == app.config['ADMIN_USER_ID']).one_or_none()
    if not query_result or len(query_result) != 2:
        return jsonify({"ok": False, "msg": "Error getting service"}), 400
    service = query_result[0]
    port_dst = query_result[1]
    ownline.do_add(app.config['LAN_NETWORK'], service, port_dst=port_dst)

    # As actioners initialization cleans all sessions, recreate the still active ones after reboot
    app.logger.info("Recreating previous still active sessions")
    # todo: clean not finished sessions
    sessions2recreate = db.session.query(Session).filter(Session.terminated == False)

    for session in sessions2recreate:
        if ownline.do_add(session.trusted_ip, session.service, port_dst=session.port_dst,
                          fixed_end_timestamp=session.end_timestamp):
            msg = f"*Session reinitialized*: {session.user.username} -> {session.service.name} from {session.trusted_ip}"
            app.logger.info(msg)
    db.session.commit()
    return jsonify({"ok": True, "msg": "OK"}), 200


########################################################################################################################
########################################################################################################################

@jwt_required(refresh=True)
@app.route('/api/v1/spa', methods=['POST'])
def spa_received():
    app.logger.info("SPA packet received from ownline-core")
    notify_service.notify_all("SPA packet received from ownline-core")
    if not request.is_json:
        return jsonify({'ok': False, "msg": "Invalid JSON"}), 400

    src_ip = request.json.get('src_ip')
    if src_ip is None or not re.compile(app.config['IP_V4_REGEX']).match(src_ip):
        app.logger.error(f"Invalid new IP message src_ip: '{src_ip}'")
        return jsonify({'ok': False, "msg": "Invalid src_ip"}), 400

    uid = request.json.get('uid')
    if uid is None or not re.compile(app.config['UUID_4_REGEX']).match(uid):
        app.logger.error(f"Invalid user id (uid): '{uid}'")
        return jsonify({'ok': False, "msg": "Invalid uid"}), 400

    ts = request.json.get('ts')
    if ts is None or not re.compile(app.config['TIMESTAMP_REGEX']).match(str(ts)):
        app.logger.error(f"Invalid timestamp (ts): '{ts}'")
        return jsonify({'ok': False, "msg": "Invalid ts"}), 400
    elif int(ts) < (round(time.time() * 1000) - app.config['MAX_SPA_DIFF_TS']):
        app.logger.error(f"Expired timestamp (ts): '{ts}'")
        return jsonify({'ok': False, "msg": "Expired ts"}), 400

    update_user_automatic_services({'trusted_ip': src_ip, 'user_id': uid})
    return jsonify({"ok": True, "msg": "OK"}), 200

########################################################################################################################
########################################################################################################################

@app.route('/api/v1/ownline/config', methods=['GET'])
@jwt_required(fresh=True)
def get_config():
    return jsonify({"ok": True, "config": {
        "host_name": app.config['BASE_HOST_NAME'],
        "invitation_url": app.config['INVITATION_URL']
    }}), 200

########################################################################################################################
########################################################################################################################