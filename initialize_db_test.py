from ownline_web import db
from ownline_web.core import models

db.drop_all()
db.create_all()


#db.session.add(models.User(public_id='8f651119-eac8-40d4-968f-487646338ba7', username='pep', password_hash='pbkdf2:sha256:80000$mjHtvw7O$4f166a70aa43dda738aee6527a94cc6a86d2fbb2bc9545bbfe1af9b2c916ae2d'))
services = [
    models.Service(id=1, public_id='60180785-b362-472c-9f67-2956ce4a82be', name='ownline', image='hass.png', protocol="https", ip_dst_lan='127.0.0.1', port_dst_lan=23303, path_dst_lan='', type='proxy',
                   custom_nginx_template="""
server {
\t#{{server_name}}

\tlisten {{port_dst}} ssl;
\t#{{next_listen_port}} 

\tinclude /opt/etc/nginx/ssl_common.conf;
    
\tallow {{ip_src}};
\t#{{next_ip_src}}
\tdeny all;

\tlocation / {
\t\troot /opt/home/ownline-pwa;
\t\tindex index.html;
\t\ttry_files $uri $uri/ /index.html;
\t}

\tlocation /api/ {
\t\tproxy_set_header Host $host;
\t\tproxy_set_header X-Real-IP $remote_addr;
\t\tproxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
\t\tproxy_set_header X-Forwarded-Proto $scheme;
\t\tproxy_http_version  1.1;

\t\tproxy_pass http://{{dst_lan}};
\t}
}
                   """),
    models.Service(id=2, public_id='1d0e9101-1241-4d69-9f52-b17ad5c51500', name='hass', image='hass.png', protocol="https", ip_dst_lan='192.168.1.50', port_dst_lan=8123, path_dst_lan='', type='proxy'),
    models.Service(id=3, public_id='7a4e82fb-c08d-4bd7-a252-bbea164187cc', name='nextcloud', image='nextcloud.png', protocol="https", ip_dst_lan='192.168.1.51', port_dst_lan=56567, path_dst_lan='/home', type='proxy'),
    models.Service(id=4, public_id='dd6aee0d-f002-463c-9fa0-554e312b83b5', name='octopi', image='octopi.png', protocol="https", ip_dst_lan='192.168.1.52', port_dst_lan=8080, path_dst_lan='', type='proxy'),
    models.Service(id=5, public_id='95474b48-8767-4e54-8e53-ace495f9cf4c', name='ssh-pi-home', image='ssh-pi-home.png', protocol="ssh", ip_dst_lan='192.168.1.53', port_dst_lan=22, path_dst_lan='', type='port_forwarding'),
    models.Service(id=6, public_id='3ec880ff-bd10-413c-8ef3-5eafa5560ade', name='ssh-pc', image='ssh-pc.png', protocol="ssh", ip_dst_lan='192.168.1.54', port_dst_lan=22, path_dst_lan='', type='port_forwarding'),
    models.Service(id=7, public_id='6bd82729-a2ea-465e-9fd1-fa078b817226', name='torrent', image='plex.png', protocol="https", ip_dst_lan='192.168.1.55', port_dst_lan=58393, path_dst_lan='', type='proxy')
]
#db.session.bulk_save_objects(services)
db.session.add_all(services)


user = models.User(public_id='7b93cf92-08fd-4fed-8403-6b858ee1ad0c', username='pep', avatar='pep.png', password_hash='pbkdf2:sha256:80000$IUqvCzBs$0dc00860656df84594e9bb8ac3ca7b620a93bdf4a394a961d4a29194f32257c5')
db.session.add(user)

user2 = models.User(public_id='dccd0054-553d-447c-aa9f-47c5609038d9', username='test', password_hash='pbkdf2:sha256:80000$IUqvCzBs$0dc00860656df84594e9bb8ac3ca7b620a93bdf4a394a961d4a29194f32257c5')
db.session.add(user2)


user_services = [
    models.UserService(service_id=1, user=user, automatic=True, port_dst=33890),
    models.UserService(service_id=2, user=user, automatic=False, port_dst=61888),
    models.UserService(service_id=3, user=user, automatic=False, port_dst=62999),
    models.UserService(service_id=4, user=user, automatic=False, port_dst=None),
    models.UserService(service_id=5, user=user, automatic=False, port_dst=None),
    models.UserService(service_id=6, user=user, automatic=False, port_dst=None),
    models.UserService(service_id=7, user=user, automatic=False, port_dst=None),
    models.UserService(service_id=3, user=user2, automatic=False, port_dst=62998)
]

db.session.add_all(user_services)

#db.session.execute(models.UserService.update().values(persistent=True).where(models.UserService.service_id.in_(1, 2, 3)))
#db.session.query(models.UserService).filter(models.UserService.user_id == 1).filter(models.UserService.service_id.in_((1, 2, 3))).update({"persistent": True})
db.session.commit()
