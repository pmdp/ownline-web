from ownline_web import app, ownline
from ownline_web import db, notify_service
from ownline_web.core.models import Service, Session, User, UserService
import datetime


def update_user_automatic_services(token):
    trusted_ip = token['trusted_ip']
    user_public_id = token['user_id']
    duration = app.config.get('AUTOMATIC_SESSION_DURATION')

    user = User.query.filter_by(public_id=user_public_id, active=True).one_or_none()
    if not user:
        app.logger.warn(f"No active user with public_id: {user_public_id}")
        return

    app.logger.info(f"Updating '{user.username}' automatic services with new IP: '{trusted_ip}'")

    """
    SELECT services.*, sessions.id FROM users
    JOIN user_service ON users.id = user_service.user_id AND user_service.persistent = 1
    JOIN services ON user_service.service_id = services.id AND services.port_dst IS NOT NULL;
    LEFT OUTER JOIN sessions ON services.id = sessions.service_id AND sessions.terminated = 0 AND sessions.automatic = 1;
    """

    user_services = db.session.query(Service, UserService.port_dst, Session) \
        .join(UserService, db.and_(UserService.service_id == Service.id, UserService.user_id == user.id,
                                   UserService.automatic == True)) \
        .outerjoin(Session, db.and_(Session.service_id == UserService.service_id, Session.user_id == user.id,
                                    Session.terminated == False, Session.automatic == True)) \
        .group_by(Service.id, UserService.port_dst, Session.id) \
        .all()
    for user_service in user_services:
        if user_service.Session:
            app.logger.debug(f"There is already an automatic session to '{user_service.Service.name}'")
            update_session(trusted_ip, user, user_service, duration)
        else:
            create_new_session(trusted_ip, user, user_service, duration)


def update_session(trusted_ip, user, user_service, duration):
    if user_service.Session.trusted_ip != ownline.get_ip_src(trusted_ip):
        app.logger.info(
            f"Updating session to {user_service.Session.service.name} with new IP: {ownline.get_ip_src(trusted_ip)}")
        ownline.do_del(user_service.Session)
        result = ownline.do_add(trusted_ip, user_service.Service, user_service.port_dst, duration)
        if result:
            user_service.Session.trusted_ip = result['trusted_ip']
            user_service.Session.end_timestamp = datetime.datetime.utcfromtimestamp(result['end_timestamp'])
            db.session.commit()
            msg = f"*Session IP and end timestamp updated*: _{user.username}_ -> {user_service.Service.name}, from {result['trusted_ip']} for {result['duration']} min"
            app.logger.info(msg)
            notify_service.notify_all(msg)
        else:
            app.logger.info(f"Error updating session: {user_service.Session.public_id}")
    else:
        user_service.Session.end_timestamp = datetime.datetime.utcfromtimestamp(
            ownline.calculate_end_timestamp(duration))
        db.session.commit()
        msg = f"*Session end timestamp updated*: _{user.username}_ -> {user_service.Service.name}, from {ownline.get_ip_src(trusted_ip)} for {duration} min"
        app.logger.debug(msg)
        notify_service.notify_all(msg)


def create_new_session(trusted_ip, user, user_service, duration):
    app.logger.debug(f"Creating new automatic session to '{user_service.Service.name}'")
    result = ownline.do_add(trusted_ip, user_service.Service, user_service.port_dst, duration)
    if result:
        new_session = Session(public_id=result['session_public_id'],
                              service_id=user_service.Service.id,
                              port_dst=result['port_dst'],
                              duration=result['duration'],
                              end_timestamp=datetime.datetime.utcfromtimestamp(result['end_timestamp']),
                              trusted_ip=result['trusted_ip'],
                              automatic=True)
        user.sessions.append(new_session)
        db.session.commit()
        msg = f"*New automatic session created*: _{user.username}_ -> {user_service.Service.name}, from {result['trusted_ip']} for {result['duration']} min"
        app.logger.info(msg)
        notify_service.notify_all(msg)
    else:
        app.logger.error("Error creating session")