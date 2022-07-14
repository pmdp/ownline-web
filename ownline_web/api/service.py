from ownline_web import app
from ownline_web import db
from ownline_web.core.models import Service, UserService
from flask import request, jsonify
from flask_jwt_extended import (jwt_required, current_user)
import re




########################################################################################################################
# SERVICES

@app.route('/api/v1/service', methods=['GET'])
@jwt_required(fresh=True)
def get_all_user_services():
    response = []
    # todo: serialize all services at once: https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
    user_services = db.session.query(UserService).with_parent(current_user).all()
    for user_service in user_services:
        service = user_service.service.serialize()
        service['automatic'] = user_service.automatic
        service['port_dst'] = user_service.port_dst
        response.append(service)
    return jsonify({"services": response}), 200


# todo: change this POST "service" to "user_service" update info

@app.route('/api/v1/service', methods=['POST'])
@jwt_required(fresh=True)
def post_service():
    if not request.is_json:
        return jsonify({'ok': False, "msg": "Invalid JSON"}), 400

    service_public_id = request.json.get('public_id')

    if not service_public_id or not re.compile(app.config['UUID_4_REGEX'], re.I).match(str(service_public_id)):
        return jsonify({"ok": False, "msg": "Invalid service_id"}), 400

    user_service = db.session.query(UserService).with_parent(current_user)\
        .join(UserService.service).filter(Service.public_id == service_public_id)\
        .one_or_none()
    if not user_service:
        return jsonify({"ok": False, "msg": "Error getting service"}), 400
    else:
        automatic = request.json.get('automatic')
        if automatic is not None and isinstance(automatic, bool):
            user_service.automatic = automatic
        else:
            return jsonify({"ok": False, "msg": "Bad 'automatic' parameter"}), 400
        port_dst = request.json.get('port_dst')
        if port_dst is not None and isinstance(port_dst, int):
            if port_dst != user_service.port_dst:
                user_service.port_dst = port_dst
        else:
            return jsonify({"ok": False, "msg": "Bad 'port_dst' parameter"}), 400
        db.session.commit()
        return jsonify({"ok": True, "msg": "OK updating service"}), 200



########################################################################################################################
########################################################################################################################