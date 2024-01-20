import secrets

from Client.ServerErrorException import ServerErrorException
from utils import send_request, bold, GREEN, color, unpack_key_base64, hash_password_hex, decrypt_aes_cbc
from config import __user_creds_filename__, __kdc_server_port__, __kdc_server_ip__, __msg_server_port__, \
    __msg_server_ip__


def register_new_user(user_name, user_pass):
    # request to server - new connection
    request = {
        'header': {
            'client_id': 'undefined',
            'version': 24,
            'code': 1025
        }, 'payload': {
            'name': user_name,
            'password': user_pass
        }
    }

    response = send_request(__kdc_server_ip__, __kdc_server_port__, request)
    print(response)
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
        raise ServerErrorException()

    else:  # unknown response
        print("Unknown response from server: ", response)
        raise ServerErrorException()


def get_servers_list(client):
    request = {
        'header': {
            'client_id': client["client_id"],
            'version': 24,
            'code': 1026
        }
    }

    response = send_request(__kdc_server_ip__, __kdc_server_port__, request)
    servers_list = response['payload']['servers_list']

    return servers_list


# request to KDC - ask for symmetric key
def get_symmetric_key_kdc(client_id, client_password, server_id):
    # Generate a random nonce (16 bytes)
    nonce = secrets.token_hex(16)

    request = {
        'header': {
            'client_id': client_id,
            'version': 24,
            'code': 1028
        },
        'payload': {
            'client_id': client_id,
            'server_id': server_id,
            'nonce': nonce
        }
    }

    response = send_request(__kdc_server_ip__, __kdc_server_port__, request)
    print("response:", response)

    symmetric_key = response['payload']['symmetric_key']
    iv = unpack_key_base64(symmetric_key['iv'])
    encrypted_aes_key = unpack_key_base64(symmetric_key['aes_key'])

    # FIXME:
    client_password_hash = hash_password_hex(client_password)
    decrypted_aes_key = decrypt_aes_cbc(client_password_hash, iv, encrypted_aes_key)
    ticket = response['payload']['ticket']

    return decrypted_aes_key, ticket


# send symmetric key to messages server
def send_symmetric_key_msg_server(client_id, aes_key, ticket):
    request = {
        'header': {
            'code': 1028
        }, 'payload': {
            'authenticator': {
                'version': 'version',
                'client_id': 'client_id',
                'server_id': 'server_id',
                'timestamp': 'timestamp',
            }, 'ticket': ticket
        }
    }
    response = send_request(__msg_server_ip__, __msg_server_port__, request)
    print(response)


def send_message(client_id, client_password, server_id, message):
    aes_key, ticket = get_symmetric_key_kdc(client_id, client_password, server_id)
    send_symmetric_key_msg_server(client_id, aes_key, ticket)

    request = {
        'header': {
            'code': 1029
        }, 'payload': {
            'message_size': 'message_size',
            'iv': 'iv',
            'message_content': 'message_content'
        }
    }
    response = send_request(__msg_server_ip__, __msg_server_port__, request)
    print(response)

