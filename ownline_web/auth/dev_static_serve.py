from .. import app, notify_service
from flask import Response, request, send_from_directory
from flask_jwt_extended import (jwt_optional, current_user)
import os

basedir = os.path.abspath(os.path.join(os.path.dirname(__package__), 'frontend/webapp'))

# IMPORTANT: DO NOT USE THIS FILE IN PRODUCTION


@app.route('/', methods=['GET'])
#@jwt_optional
def index_routing():
    app.logger.info("GET request to /")
    # todo: get_jwt() for check if token is allowed to load web frontend, when access from browser cookies
    #if current_user:
    if request.headers.get('Authorization') or request.cookies.get('access_token_cookie'):
        return send_from_directory(basedir + '/private/', 'index.html')
    else:
        return send_from_directory(basedir + '/public/', 'index.html')


@app.route('/<path:file_path>', methods=['GET'])
#@jwt_optional
def static_routing(file_path):
    # todo: get_jwt() for check if token is allowed to load web frontend, when access from browser cookies
    # if current_user:
    if request.headers.get('Authorization') or request.cookies.get('access_token_cookie'):
        return send_from_directory(basedir + '/private/', file_path)
    else:
        return send_from_directory(basedir + '/public/', 'index.html')
