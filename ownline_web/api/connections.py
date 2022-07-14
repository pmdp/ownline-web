from ownline_web import app
from ownline_web.core.models import Connection
from flask import jsonify
from flask_jwt_extended import (jwt_required, current_user)


@app.route('/api/v1/connection', methods=['GET'])
@jwt_required(fresh=True)
def get_all_user_connections():
    # todo: pagination: http://flask-sqlalchemy.pocoo.org/2.3/api/#flask_sqlalchemy.BaseQuery.paginate
    # todo: serialize all sessions at once https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
    connections = Connection.query.with_parent(current_user).order_by(Connection.date_modified.desc()).all()
    response = []
    for connection in connections:
        response.append(connection.serialize())
    return jsonify({"connections": response}), 200