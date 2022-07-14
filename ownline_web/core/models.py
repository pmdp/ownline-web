from ownline_web import db
import datetime
from datetime import timezone


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class User(Base):
    __tablename__ = 'users'

    public_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(10), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), nullable=False, default='default.png')
    active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_success = db.Column(db.DateTime)
    login_attempts_count = db.Column(db.Integer, default=0)
    last_login_attempt = db.Column(db.DateTime)

    # Uses one to many relationship
    sessions = db.relationship("Session", back_populates="user")
    # Uses one to many relationship
    connections = db.relationship("Connection", back_populates="user")
    # Uses one to many relationship
    invitations = db.relationship("Invitation", back_populates="user")
    # Uses one to many relationship to user_services association table (many to many)
    services = db.relationship("UserService", back_populates="user")

    def __repr__(self):
        return '<User %r>' % self.username


class Service(Base):
    __tablename__ = 'services'

    public_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    image = db.Column(db.String(255), nullable=False)
    protocol = db.Column(db.String(30))
    transport_protocol = db.Column(db.String(30), nullable=False, default='tcp')
    ip_dst_lan = db.Column(db.String(30))
    port_dst_lan = db.Column(db.Integer)
    path_dst_lan = db.Column(db.String(255))
    type = db.Column(db.String(20))
    connection_upgrade = db.Column(db.Boolean, nullable=False, default=False)
    custom_nginx_template = db.Column(db.Text)

    # One to many relationship to user_services association table (many to many)
    users = db.relationship("UserService", back_populates="service")
    # One to many relationship
    sessions = db.relationship("Session", back_populates="service")
    # One to many relationship
    invitations = db.relationship("Invitation", back_populates="service")

    def __repr__(self):
        return '<Service %r>' % self.name

    def serialize(self):
        return {'public_id': self.public_id,
                'name': self.name,
                'image': self.image,
                'protocol': self.protocol,
                'transport_protocol': self.transport_protocol,
                'connection_upgrade': self.connection_upgrade,
                'path_dst_lan': self.path_dst_lan}

    def serialize_to_ownline_web(self):
        return {'name': self.name,
                'protocol': self.protocol,
                'transport_protocol': self.transport_protocol,
                'ip_dst_lan': self.ip_dst_lan,
                'port_dst_lan': self.port_dst_lan,
                'type': self.type,
                'connection_upgrade': self.connection_upgrade,
                'custom_nginx_template': self.custom_nginx_template}


class UserService(db.Model):
    __tablename__ = 'user_service'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), primary_key=True)

    # True if its a service which we want to create an automatic session
    # when a signal (user/ip) is sent from a trusted device
    automatic = db.Column(db.Boolean, nullable=False, default=False)
    # The public static port that the user has with this automatic service
    port_dst = db.Column(db.Integer, nullable=True, default=None, unique=True)

    # One to one relationship
    service = db.relationship("Service", back_populates="users")
    # One to one relationship
    user = db.relationship("User", back_populates="services")


class Session(Base):
    __tablename__ = 'sessions'

    public_id = db.Column(db.String(255), nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    port_dst = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    end_timestamp = db.Column(db.DateTime, nullable=False)
    trusted_ip = db.Column(db.String(20), nullable=False)
    automatic = db.Column(db.Boolean, default=False, nullable=False)
    terminated = db.Column(db.Boolean, default=False, nullable=False)

    # One to many relationship
    user = db.relationship("User", back_populates="sessions")
    # One to many relationship
    service = db.relationship("Service", back_populates="sessions")

    def __repr__(self):
        return '<Session %r>' % self.public_id

    def serialize(self):
        return {
            'public_id': self.public_id,
            'port_dst': self.port_dst,
            'duration': self.duration,
            'end_timestamp': self.end_timestamp.replace(tzinfo=timezone.utc).timestamp(),
            'trusted_ip': self.trusted_ip,
            'terminated': self.terminated,
            'automatic': self.automatic,
            'service_id': self.service.public_id
        }

    def serialize_to_ownline_web(self):
        return {
            'port_dst': self.port_dst,
            'trusted_ip': self.trusted_ip,
            'service': self.service.serialize_to_ownline_web()
        }


class Connection(Base):
    __tablename__ = 'connections'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    remote_addr = db.Column(db.String(20), nullable=False)
    user_agent = db.Column(db.String(255), nullable=False)

    # One to many relationship
    user = db.relationship("User", back_populates="connections")

    def __repr__(self):
        return '<Connection %r>' % self.id

    def serialize(self):
        return {
            'remote_addr': self.remote_addr,
            'user_agent': self.user_agent
        }


class Invitation(Base):
    __tablename__ = 'invitations'

    public_id = db.Column(db.String(255), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    sec_token = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=False)
    message = db.Column(db.String(255), nullable=True)
    activation_timestamp = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=False)
    end_timestamp = db.Column(db.DateTime, nullable=False)

    # One to many relationship
    user = db.relationship("User", back_populates="invitations")
    # One to many relationship
    service = db.relationship("Service", back_populates="invitations")

    def __repr__(self):
        return '<Invitation %r>' % self.id

    def serialize(self):
        return {
            'public_id': self.public_id,
            'active': self.active,
            'sec_token': self.sec_token,
            'message': self.message,
            'activation_timestamp': self.activation_timestamp,
            'end_timestamp': self.end_timestamp.replace(tzinfo=timezone.utc).timestamp(),
            'duration': self.duration,
            'service_id': self.service_id,
        }




