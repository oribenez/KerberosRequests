import inspect
import json
import struct
import time
from datetime import datetime, timedelta

from Crypto.Random import get_random_bytes

from lib.config import salt
from config import __api_version__
from lib.utils import pack_key_hex, hash_password, encrypt_aes_cbc, pack_key_base64, unpack_key_hex, unpack_key_base64, \
    send, RESPONSE, color, RED, decrypt_aes_cbc
from utils import generate_random_uuid
import KDC.db.models as models


def register_client(connection, req):
    try:
        print('req: ', req)
        # add client to clients list
        client_id = generate_random_uuid()
        print("#####$#$#$#client_id: ", client_id)
        name = req['payload']['name']
        password_hash = hash_password(req['payload']['password'], salt)
        timestamp = time.time()
        client = {
            "client_id": client_id,
            "name": name,
            "password_hash": password_hash,
            "last_seen": timestamp
        }
        print('client: ', client)
        models.db["clients"].add_client(client)

        # response to client
        response = {
            'header': {
                'version': __api_version__,
                'code': 1600,
            }, 'payload': {
                'client_id': client_id
            }
        }
        print('[SUCCESS] register_client()')

    except Exception as e:
        print(f"Exception in function: {inspect.currentframe().f_code.co_name}")
        print(f"Exception message: {str(e)}")

        response = {
            'header': {
                'version': __api_version__,
                'code': 1601,
            }
        }

    send(connection, RESPONSE, response)


def register_server(connection, req):
    print("register_server()")
    try:
        # add client to clients list
        server_id = generate_random_uuid()

        server = {
            "server_id": server_id,
            "name": req["payload"]["name"],
            "server_ip": req["payload"]["server_ip"],
            "server_port": req["payload"]["server_port"],
            "aes_key": req["payload"]["aes_key"],
        }

        models.db["servers"].add_server(server)

        # response to client
        response = {
            'header': {
                'version': __api_version__,
                'code': 16000,
            }, 'payload': {
                'server_id': server_id
            }
        }

    except Exception as e:
        print(f"Exception in function: {inspect.currentframe().f_code.co_name}")
        print(f"Exception message: {str(e)}")

        response = {
            'header': {
                'version': __api_version__,
                'code': 1601,
            }
        }

    send(connection, RESPONSE, response)


def get_servers_list(connection, req):
    print("get_servers_list()")
    servers_list = models.db["servers"].get_all_servers()

    response = {
        'header': {
            'version': __api_version__,
            'code': 1602,
        }, 'payload': {}
    }
    for ind, server in enumerate(servers_list):
        response['payload']['server_id__' + str(ind)] = server['server_id']
        response['payload']['server_name__' + str(ind)] = server['name']
        response['payload']['server_ip__' + str(ind)] = server['server_ip']
        response['payload']['server_port__' + str(ind)] = server['server_port']
    print("Response: ", response)
    send(connection, RESPONSE, response)


def get_symmetric_key(connection, req):
    print("get_symmetric_key()")
    # unpack request values
    client_id = req["header"]["client_id"]
    server_id = req["payload"]["server_id"]
    nonce = req["payload"]["nonce"]  # TODO: handle nonce
    print('header: ', req["header"])
    # # Prepare response to client
    print("sav1")

    # Generate AES key SHA-256
    session_aes_key = get_random_bytes(32)

    # client_password_hash - a hash of the client password that he used at registration
    client_password_hash = models.db["clients"].get_password_hash_by_client_id(client_id)
    print('client_password_hash: ', client_password_hash)

    # Encrypted [Nonce] with [Client key]
    iv__c, encrypted_nonce__with_c = encrypt_aes_cbc(key=client_password_hash, data=nonce)

    # Encrypted [Session key] with [Client key]
    _, encrypted_session_aes_key__with_c = encrypt_aes_cbc(key=client_password_hash, data=session_aes_key, iv=iv__c)

    print('server_id: ', server_id)
    # server AES key generated at server registration
    server_aes_key = models.db["servers"].get_aes_key_by_server_id(server_id)
    print('server_aes_key: ', server_aes_key)
    # Encrypted [Session key] with [Server key]
    ticket_iv, encrypted_session_aes_key__with_s = encrypt_aes_cbc(key=server_aes_key, data=session_aes_key)

    print("sav3")
    timestamp = time.time()
    expiration_time = str(int(time.time() + 5 * 60)).encode('utf-8')  # Now + 5 minutes (seconds) & Pack the timestamp into bytes
    print("sav4")
    # Encrypt [expiration_time] with the key [server_aes_key] using the *same* IV as before
    _, encrypted_expiration_time__with_s = encrypt_aes_cbc(key=server_aes_key, data=expiration_time, iv=ticket_iv)
    print("sav5")
    response = {
        'header': {
            'version': __api_version__,
            'code': 1603,
        }, 'payload': {
            'client_id': client_id,
            'symmetric_key': {
                'symm_iv': iv__c,
                'nonce': encrypted_nonce__with_c,
                'aes_key': encrypted_session_aes_key__with_c,
            }, 'ticket': {
                'version': __api_version__,
                'client_id': client_id,
                'server_id': server_id,
                'timestamp': timestamp,
                'ticket_iv': ticket_iv,
                'aes_key': encrypted_session_aes_key__with_s,
                'expiration_time': encrypted_expiration_time__with_s
            }
        }
    }
    print(color('get_symmetric_key', RED))
    print('symm__iv: ', iv__c)
    print('symm__aes_key: ', encrypted_session_aes_key__with_c)
    print('ticket__iv: ', ticket_iv)
    print('ticket__aes_key: ', encrypted_session_aes_key__with_s)
    print(f'server_aes_key({len(server_aes_key)}): ', server_aes_key)
    print(f'ticket__expiration_time ({len(encrypted_expiration_time__with_s)}): ', encrypted_expiration_time__with_s)

    send(connection, RESPONSE, response)


def not_found_controller(connection, req):
    raise ValueError("Invalid request code")
