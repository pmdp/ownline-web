import click
from flask.cli import FlaskGroup
import csv
from ownline_web import app, db
from ownline_web.core import models

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("initialize_db")
@click.argument('users_csv', type=click.Path(exists=True))
@click.argument('services_csv', type=click.Path(exists=True))
def initialize_db(users_csv, services_csv):
    users_csv_file = click.open_file(click.format_filename(users_csv), 'r')
    users_csv_reader = csv.DictReader(users_csv_file, delimiter=',')
    for user in users_csv_reader:
        print("Adding new user", end=' ')
        user = models.User(public_id=user['public_id'], username=user['username'],
                           password_hash=user['password_hash'], avatar=user['avatar'])
        db.session.add(user)
        print("User added: {}".format(user))
    services_csv_file = click.open_file(click.format_filename(services_csv), 'r')
    services_csv_reader = csv.DictReader(services_csv_file, delimiter=',')
    for service in services_csv_reader:
        print("Adding new service", end=' ')
        new_service = models.Service(public_id=service['public_id'], name=service['name'], image=service['image'],
                       protocol=service['protocol'], ip_dst_lan=service['ip_dst_lan'],
                       port_dst_lan=service['port_dst_lan'], path_dst_lan=service['path_dst_lan'],
                       type=service['type'], connection_upgrade=bool(int(service['connection_upgrade'])),
                                     custom_nginx_template=service['custom_nginx_template'])
        db.session.add(new_service)
        for user_name in service['users'].split(','):
            user = models.User.query.filter_by(username=user_name).one_or_none()
            if 'port_dst' in service.keys() and service['port_dst'] != '':
                port_dst = int(service['port_dst'])
            else:
                port_dst = None
            user_service = models.UserService(service=new_service, user=user,
                                              automatic=bool(int(service['automatic'])),
                                              port_dst=port_dst)
            db.session.add(user_service)

    db.session.commit()


if __name__ == "__main__":
    cli()