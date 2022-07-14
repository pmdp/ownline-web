import hashlib
import hmac
import json
import ssl
import uuid
import re
import time

import socket

from flask import _app_ctx_stack
from ownline_web.core.exceptions import MessageValidationException


class OwnlineAction(object):
    """
    Actioner for verifying, processing and executing requests
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.teardown_appcontext(self.teardown)

    def teardown(self, exception):
        ctx = _app_ctx_stack.top
        if hasattr(ctx, 'ownline'):
            ctx.ownline.close()

    def initialize(self):
        cmd = {
            'action': 'ini'
        }
        response = self.send_ownline_cmd_to_core(cmd)
        if response["ok"]:
            self.app.logger.info(f"Correctly initialize ownline-core, with response: {response}")
        else:
            self.app.logger.error(f"Error initializing ownline-core, with response: {response}")

    def ping(self):
        cmd = {
            'action': 'ping'
        }
        response = self.send_ownline_cmd_to_core(cmd)
        if response["ok"]:
            self.app.logger.debug(f"Correctly ping ownline-core, with response: {response}")
        else:
            self.app.logger.error(f"Error ping ownline-core, with response: {response}")
        return response

    @staticmethod
    def get_new_session_id():
        return str(uuid.uuid4())

    @staticmethod
    def calculate_end_timestamp(duration):
        #return int((datetime.datetime.utcnow() + datetime.timedelta(minutes=duration)).strftime('%s'))
        return round((time.time() + (duration * 60.0)))

    def get_ip_src(self, ip_src):
        return ip_src

    def do_add(self, trusted_ip, service, port_dst=None, duration=None, fixed_end_timestamp=None):
        result = False
        try:
            if not re.compile(self.app.config['IP_V4_REGEX']).match(trusted_ip) \
                    and not trusted_ip == self.app.config['LAN_NETWORK']:
                raise MessageValidationException("Invalid trusted_ip: {}".format(trusted_ip))

            trusted_ip = self.get_ip_src(trusted_ip)

            if duration is None or type(duration) != int or duration == 0:
                duration = self.app.config['DEFAULT_SESSION_DURATION']
            elif duration < 1 or duration > self.app.config['MAX_SESSION_DURATION']:
                raise MessageValidationException(f"Invalid duration: {duration} min")

            cmd = {
                'action': 'add',
                'payload': {
                    'trusted_ip': trusted_ip,
                    'service': service.serialize_to_ownline_web(),
                    'port_dst': port_dst
                }
            }
            ownline_core_result = self.send_ownline_cmd_to_core(cmd)

            if ownline_core_result["ok"]:
                session_id = self.get_new_session_id()
                if fixed_end_timestamp:
                    end_timestamp = fixed_end_timestamp
                else:
                    end_timestamp = self.calculate_end_timestamp(duration)
                if port_dst is None and 'port_dst' in ownline_core_result.keys():
                    port_dst = ownline_core_result['port_dst']

                result = {'session_public_id': session_id,
                          'trusted_ip': trusted_ip,
                          'port_dst': port_dst,
                          'end_timestamp': end_timestamp,
                          'duration': duration
                          }
        except MessageValidationException as e2:
            self.app.logger.error(e2)
        except Exception as e3:
            self.app.logger.error(e3)
        finally:
            self.app.logger.debug(f"Result from ownline: {result}")
            return result

    def do_del(self, session):
        result = False
        try:
            cmd = {
                'action': 'del',
                'payload': session.serialize_to_ownline_web()
            }
            result = self.send_ownline_cmd_to_core(cmd)
        except MessageValidationException as e2:
            self.app.logger.error(e2)
        except Exception as e3:
            self.app.logger.error(e3)
        finally:
            return result

    def do_flush(self):
        self.app.logger.debug("Removing all sessions")
        result = False
        try:
            cmd = {
                'action': 'flush'
            }
            result = self.send_ownline_cmd_to_core(cmd)
            if result:
                self.app.logger.info("All sessions removed")
                return result
        except MessageValidationException as e2:
            self.app.logger.error(e2)
        except Exception as e3:
            self.app.logger.error(e3)
        finally:
            return result

    def send_ownline_cmd_to_core(self, cmd):
        dumped_cmd = json.dumps(cmd, indent=None, separators=(',', ':'))
        sign = hmac.new(self.app.config['HMAC_KEY'], dumped_cmd.encode('utf-8'), hashlib.sha512).hexdigest()
        final_cmd = sign.encode('utf-8') + dumped_cmd.encode('utf-8')

        response = {'ok': False}

        try:
            # PROTOCOL_TLS_CLIENT requires valid cert chain and hostname
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            # todo: check valid certificate
            # context.load_verify_locations('path/to/cabundle.pem')
            context.load_cert_chain(certfile=self.app.config['CMD_SERVER_CERT_PATH'],
                                    keyfile=self.app.config['CMD_SERVER_KEY_PATH'],
                                    password=self.app.config['CMD_SERVER_CERT_PASSWORD'])
            context.check_hostname = False
            # context.verify_mode = ssl.CERT_REQUIRED
            context.verify_mode = ssl.CERT_NONE

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
                with context.wrap_socket(sock) as ssock:
                    print(ssock.version())
                    ssock.settimeout(15)
                    ssock.connect((self.app.config['CMD_SERVER_IP'], self.app.config['CMD_SERVER_PORT']))
                    self.app.logger.info(f"Final Message to SEND: {final_cmd}")
                    ssock.sendall(final_cmd)
                    response = ssock.recv(1024)
                    self.app.logger.info(f"Received response: {response}")
                    response = json.loads(response)
        except Exception as e:
            self.app.logger.error(e)
        finally:
            return response

    def get_ip_src(self, ip_src):
        if ip_src == self.app.config['LAN_NETWORK']:
            return ip_src
        elif ip_src[-3:] != '/32':
            return ip_src + '/32'
        else:
            return ip_src