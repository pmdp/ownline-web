from .. import app, notify_service
from flask import Response, request
from werkzeug.security import safe_join
from flask_jwt_extended import (jwt_optional, current_user)

from ..utils.remote_addr import get_remote_addr

"""
@jwt_optional

A decorator to optionally protect a Flask endpoint
If an access token in present in the request, this will call the endpoint with get_jwt_identity() having the identity 
of the access token. If no access token is present in the request, this endpoint will still be called, 
but get_jwt_identity() will return None instead.
If there is an invalid access token in the request (expired, tampered with, etc), this will still call the appropriate 
error handler instead of allowing the endpoint to be called as if there is no access token in the request.
"""


@app.route('/', methods=['GET'])
@jwt_optional
def index_routing():
    user_agent = request.headers.get('User-Agent')
    app.logger.info("GET request to /")
    response = Response()
    # todo: get_jwt() for check if token is allowed to load web frontend, when access from browser cookies
    if current_user:
        response.headers['X-Accel-Redirect'] = '/private/index.html'
        notify_service.notify_all(
            "*Access* from {} -> *private*\n*User-Agent*: `{}`".format(get_remote_addr(request), user_agent))
    else:
        response.headers['X-Accel-Redirect'] = '/public/index.html'
        notify_service.notify_all(
            "*Access* from {} -> *public*".format(get_remote_addr(request)))
    return response


@app.route('/<path:file_path>', methods=['GET'])
@jwt_optional
def static_routing(file_path):
    response = Response()
    # todo: get_jwt() for check if token is allowed to load web frontend, when access from browser cookies
    if current_user:
        app.logger.info("User is authorized, serving: {}".format(file_path))
        # if user is authorized, give him what is requesting by a nginx send file header
        response.headers['X-Accel-Redirect'] = safe_join('/private/', str(file_path))
    else:
        response.status_code = 404
    return response
