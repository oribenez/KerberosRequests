import secrets
import sys
import time

from lib.ServerException import ServerException
from lib.utils import send_request, hash_password, decrypt_aes_cbc, \
    encrypt_aes_cbc
from config import __user_creds_filename__, __kdc_server_port__, __kdc_server_ip__, __msg_server_port__, \
    __msg_server_ip__
from lib.config import __api_version__
from lib.config import salt


def register_new_user(user_name, user_pass):
    print('register_new_user')
    # request to server - new connection
    request = {
        'header': {
            'client_id': 'undefined',
            'version': __api_version__,
            'code': 1024
        }, 'payload': {
            'name': user_name,
            'password': user_pass
        }
    }

    response = send_request(__kdc_server_ip__, __kdc_server_port__, request)
    print('response: ', response)

    response_code = response["header"]["code"]
    if response_code == 1600:  # registration success
        print("[1600] Registration success")
        # save user to file
        with open(__user_creds_filename__, "w") as file:
            client_id = response["payload"]["client_id"]
            file.write(f"{__kdc_server_ip__}:{__kdc_server_port__}\n{user_name}\n{client_id}")

        client = {
            'ip': __kdc_server_ip__, 'port': __kdc_server_port__, 'name': user_name, 'client_id': client_id
        }

        return client

    elif response_code == 1601:  # registration failed
        print("[1601] Registration failed")
        raise ServerException()

    else:  # unknown response
        print("Unknown response from server: ", response)
        raise ServerException()


def get_servers_list(client):
    print('get_servers_list()')
    request = {
        'header': {
            'client_id': client["client_id"],
            'version': __api_version__,
            'code': 1026
        }
    }

    response = send_request(__kdc_server_ip__, __kdc_server_port__, request)
    print("Response payload: ", response['payload'])

    # expecting a list in payload
    servers_list = response['payload']  # FIXME

    return servers_list


# request to KDC - ask for symmetric key
def get_symmetric_key_kdc(client_id, client_password, server_id):
    # Generate a random nonce (16 bytes)
    nonce = secrets.token_hex(16)

    request = {
        'header': {
            'client_id': client_id,
            'version': __api_version__,
            'code': 1027
        },
        'payload': {
            'client_id': client_id,
            'server_id': server_id,
            'nonce': nonce
        }
    }

    response = send_request(__kdc_server_ip__, __kdc_server_port__, request)
    print("response:", response)
    if response['header']['code'] != 1603:
        raise ServerException()

    symmetric_key = response['payload']['symmetric_key']
    iv = symmetric_key['symm_iv']
    encrypted_session_aes_key = symmetric_key['aes_key']
    client_password_hash = hash_password(client_password, salt)
    decrypted_session_aes_key = decrypt_aes_cbc(client_password_hash, iv, encrypted_session_aes_key)

    ticket = response['payload']['ticket']

    return iv, decrypted_session_aes_key, ticket


# send symmetric key to messages server
def send_symmetric_key_msg_server(client_id, server_id, session_aes_key, ticket):
    print('send_symmetric_key_msg_server()')
    timestamp = str(time.time())
    iv, encrypted_version__with_session_key = encrypt_aes_cbc(key=session_aes_key,
                                                              data=str(__api_version__).encode('utf-8'))
    _, encrypted_client_id__with_session_key = encrypt_aes_cbc(key=session_aes_key, data=client_id.encode('utf-8'),
                                                               iv=iv)
    _, encrypted_server_id__with_session_key = encrypt_aes_cbc(key=session_aes_key, data=server_id.encode('utf-8'),
                                                               iv=iv)
    _, encrypted_timestamp__with_session_key = encrypt_aes_cbc(key=session_aes_key, data=timestamp.encode('utf-8'),
                                                               iv=iv)
    print('Client:')
    print('session_aes_key: ', session_aes_key)
    print('auth_iv: ', iv)
    print('version: ', encrypted_version__with_session_key)

    request = {
        'header': {
            'client_id': client_id,
            'version': __api_version__,
            'code': 1028
        }, 'payload': {
            'authenticator': {
                'auth_iv': iv,
                'version': encrypted_version__with_session_key,
                'client_id': encrypted_client_id__with_session_key,
                'server_id': encrypted_server_id__with_session_key,
                'timestamp': encrypted_timestamp__with_session_key
            }, 'ticket': ticket
        }
    }

    print("authenticator: ", {'authenticator': {
                'auth_iv': iv,
                'version': encrypted_version__with_session_key,
                'client_id': encrypted_client_id__with_session_key,
                'server_id': encrypted_server_id__with_session_key,
                'timestamp': encrypted_timestamp__with_session_key
            }})
    print("ticket: ", ticket)
    response = send_request(__msg_server_ip__, __msg_server_port__, request)
    print(response)

    # Make sure the server accepted the symmetric key
    if response["header"]["code"] != 1604:
        raise ServerException()


def send_message(client_id, client_password, server_id, message):
    iv, aes_key, ticket = get_symmetric_key_kdc(client_id, client_password, server_id)
    send_symmetric_key_msg_server(client_id, server_id, aes_key, ticket)

    _, encrypted_message = encrypt_aes_cbc(aes_key, message.encode('utf-8'), iv)
    message_size = sys.getsizeof(encrypted_message)
    print("encrypted_message: ", encrypted_message)
    request = {
        'header': {
            'client_id': client_id,
            'version': __api_version__,
            'code': 1029
        }, 'payload': {
            'message_size': message_size,
            'iv': iv,
            'message_content': encrypted_message
        }
    }
    response = send_request(__msg_server_ip__, __msg_server_port__, request)
    print(response)
