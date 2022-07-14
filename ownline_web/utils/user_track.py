from ownline_web import db
from ownline_web.core.models import User, Connection
from flask import request

from ownline_web.utils.remote_addr import get_remote_addr


def update_user_connections(user_id):
    user = User.query.get(user_id)
    remote_addr = get_remote_addr(request)
    user_agent = request.headers.get('User-Agent')
    last_connection = Connection.query.with_parent(user).order_by(Connection.date_modified.desc()).first()
    if not last_connection or last_connection.remote_addr != remote_addr or last_connection.user_agent != user_agent:
        # If its the first access or values changed from last connection, create new connection
        connection = Connection(remote_addr=remote_addr, user_agent=user_agent)
        user.connections.append(connection)
        db.session.commit()
