import json
import hmac
import hashlib


user = "uuid"
trusted_ip = "ip"
secret = b'secret'


msg = {"user_id": user, "trusted_ip": trusted_ip}

dumped_msg = json.dumps(msg, separators=(',', ':')).encode('utf-8')
print(dumped_msg)

sign = hmac.new(secret, dumped_msg, hashlib.sha512).hexdigest()

result = {"signature": sign, "msg": msg}

print(json.dumps(result, separators=(',', ':')).encode('utf-8'))