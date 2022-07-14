from ownline_web import app
from ownline_web import notify_service, jwt, db
from ownline_web.core.models import User, Connection
from flask import request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
                                current_user, get_csrf_token, jwt_required)
#from flask_cors import cross_origin
from ownline_web.utils.remote_addr import get_remote_addr
from ownline_web.utils.user_track import update_user_connections
import datetime
import re


# @app.route('/login', methods=['POST'])
# def login():
#     tokens = validate_and_process_login()
#     if tokens:
#
#     else:
#         return jsonify({"ok": False, "msg": "Invalid login attempt"}), 400

@app.route('/api/v1/login', methods=['POST'])
def api_login():
    tokens = validate_and_process_login()
    if tokens:
        # If login request is from mobile (/login?mobile=1)
        if request.args.get('mobile', default=False):
            return jsonify({"ok": True, "tokens": {
                "access": tokens['access_token'],
                "refresh": tokens['refresh_token']
            }}), 200
        else:
            # If login is from browser
            max_age = app.config['JWT_ACCESS_TOKEN_EXPIRES_MINUTES'] * 60
            # todo: devolver un csrf_token que guardar en localStorage y luego enviarse como cabecera en todos los POST
            response = jsonify({"ok": True, "maxAge": max_age})
            set_access_cookies(response, tokens['access_token'], max_age=max_age)
            # set_refresh_cookies(response, refresh_token)
            return response, 200
    else:
        return jsonify({"ok": False, "msg": "Invalid login attempt"}), 400


def validate_and_process_login():
    if not request.is_json:
        return False

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    source_ip = get_remote_addr(request)

    app.logger.info("Login init from {}".format(source_ip))

    if not username or not password or len(username) > 10 or len(password) > 30:
        return False

    # if not re.compile(app.config['USERNAME_REGEX'], re.I).match(str(username)) \
    #         or not re.compile(app.config['PASSWORD_REGEX'], re.I).match(str(password)):
    #     return False

    user = User.query.filter_by(username=username).one_or_none()
    if not user or not user.active:
        return False

    if user.login_attempts_count > app.config['MAX_LOGIN_ATTEMPTS'] \
            and user.last_login_attempt > \
            (datetime.datetime.utcnow() - datetime.timedelta(hours=app.config['LOGIN_BAN_HOURS'])):
        app.logger.warning("Max login attempts reached")
        notify_service.notify_all("*Max login attempts* reached")
        return False

    if check_password_hash(user.password_hash, password):
        msg = "*Login success* from: {}".format(source_ip)
        access_token = create_access_token(identity=user.public_id, fresh=True)
        refresh_token = create_refresh_token(identity=user.public_id)
        tokens = {'access_token': access_token, 'refresh_token': refresh_token}
        app.logger.info(msg)
        notify_service.notify_all(msg)
        update_user_connections(user.id)
        user.last_login_success = datetime.datetime.utcnow()
        user.login_attempts_count = 0
        db.session.commit()
        return tokens
    else:
        user.login_attempts_count += 1
        user.last_login_attempt = datetime.datetime.utcnow()
        db.session.commit()
        app.logger.info("Login attempt from {}".format(source_ip))
        notify_service.notify_all("*Login attempt* from {}".format(source_ip))
        return False


@app.route('/api/v1/logout', methods=['POST'])
def logout():
    response = jsonify({'logout': True})
    unset_jwt_cookies(response)
    return response, 200


@app.route('/api/v1/token/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    update_user_connections(current_user.id)
    response = {
        'access_token': create_access_token(identity=current_user.public_id, fresh=True)
    }
    return jsonify(response), 200


@app.route('/api/v1/user', methods=['GET'])
@jwt_required(fresh=True)
def get_user_info():
    return jsonify({"user": {
        "name": current_user.username,
        "avatar": current_user.avatar}})


@jwt.unauthorized_loader
def unauthorized_loader_callback(e):
    app.logger.warning("Unauthorized token: {}".format(e))
    return '', 404


@jwt.expired_token_loader
def expired_token_loader_callback(token_header, token_payload):
    app.logger.warning("Expired token")
    return '', 404


@jwt.invalid_token_loader
def invalid_token_loader_callback(e):
    app.logger.warning("Invalid token: {}".format(e))
    return '', 404


@jwt.needs_fresh_token_loader
def needs_fresh_token_loader_callback(token_header, token_payload):
    app.logger.warning("Needs fresh token")
    return '', 404


@jwt.revoked_token_loader
def revoked_token_loader_callback(token_header, token_payload):
    app.logger.warning("Revoked token")
    return '', 404


# User auto loaders at all protected methods with current_user LocalProxy
# https://flask-jwt-extended.readthedocs.io/en/latest/complex_objects_from_token.html
# This function is called whenever a protected endpoint is accessed,
# and must return an object based on the tokens identity.
# This is called after the token is verified, so you can use
# get_jwt() in here if desired. Note that this needs to
# return None if the user could not be loaded for any reason,
# such as not being found in the underlying data store
@jwt.user_lookup_loader
def user_lookup_loader(token_header, token_payload):
    identity = token_payload["sub"]
    user = User.query.filter_by(public_id=identity).one_or_none()
    if not user:
        return None
    else:
        return user


# You can override the error returned to the user if the
# user_loader_callback returns None. If you don't override
# this, # it will return a 401 status code with the JSON:
# {"msg": "Error loading the user <identity>"}.
# You can use # get_jwt() here too if desired
@jwt.user_lookup_error_loader
def custom_user_loader_error(identity):
    app.logger.error("User {} not found".format(identity))
    return '', 404


# todo: token_in_blacklist_loader(), token_verification_loader(), token_verification_failed_loader()
# todo: https://flask-jwt-extended.readthedocs.io/en/latest/api.html#flask_jwt_extended.JWTManager.token_verification_loader
# todo: put if token can access web frontend at claims (chek it at static_rounting) https://flask-jwt-extended.readthedocs.io/en/latest/add_custom_data_claims.html

