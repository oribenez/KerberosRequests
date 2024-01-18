from utils import pack_and_send
from config import __api_version__


# 'ticket': {
#     'version': __api_version__,
#     'client_id': client_id,
#     'server_id': server_id,
#     'timestamp': timestamp,
#     'ticket_iv': iv__s,
#     'aes_key': encrypted_aes_key__s,
#     'expiration_time': encrypted_expiration_time__s
# }
def send_symmetric_key(connection, req):

    authenticator = req['payload']['authenticator']
    ticket = req['payload']['ticket']

    response = {
        'header': {
            'version': __api_version__,
            'code': 1604
        }
    }
    pack_and_send(connection, response)


def send_message(connection, req):
    response = {
        'header': {
            'version': __api_version__,
            'code': 1605
        }
    }
    pack_and_send(connection, response)


def not_found_controller(connection, req):
    raise ValueError("Invalid request code")
