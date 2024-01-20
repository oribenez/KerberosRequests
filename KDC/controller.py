import inspect
import json
import struct
import time
from datetime import datetime, timedelta

from Crypto.Random import get_random_bytes

from Client.config import salt
from config import __api_version__
from utils import generate_random_uuid, hash_password_hex, pack_and_send, encrypt_aes_cbc, pack_key_base64
import KDC.db.models as models


def register_client(connection, req):
    try:
        # add client to clients list
        client_id = generate_random_uuid()
        password_hash = hash_password_hex(req["payload"]["password"], salt)
        timestamp = time.time()
        client = {
            "client_id": client_id,
            "name": req["payload"]["name"],
            "password_hash": password_hash,
            "last_seen": timestamp
        }

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

    except Exception as e:
        print(f"Exception in function: {inspect.currentframe().f_code.co_name}")
        print(f"Exception message: {str(e)}")

        response = {
            'header': {
                'version': __api_version__,
                'code': 1601,
            }
        }

    pack_and_send(connection, response)


def register_server(connection, req):
    print("register_server()")
    try:
        # add client to clients list
        server_id = generate_random_uuid()
        server = {
            "server_id": server_id,
            "name": req["payload"]["name"],
            "aes_key": req["payload"]["aes_key"],
        }

        models.db["servers"].add_server(server)

        # response to client
        response = {
            'header': {
                'version': __api_version__,
                'code': 1600,
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

    pack_and_send(connection, response)


def get_servers_list(connection, req):
    print("get_servers_list()")
    servers_list = models.db["servers"].get_all_servers()

    response = {
        'header': {
            'version': __api_version__,
            'code': 1602,
        }, 'payload': {
            'servers_list': servers_list
        }
    }
    pack_and_send(connection, response)


def get_symmetric_key(connection, req):
    print("get_symmetric_key()")
    # unpack request values
    client_id = req["header"]["client_id"]
    server_id = req["payload"]["server_id"]
    nonce = req["payload"]["nonce"]  # TODO: handle nonce

    # Prepare response to client
    print("sav1")
    sc_aes_key = models.db["servers"].get_aes_key_by_server_id(server_id)  # sc - AES key belongs to both the server and client
    # FIXME: BREAKING CHANGES: need to fix all AES keys
    # client_password_hash = a hash of the client password that he used at registration
    client_password_hash = models.db["clients"].get_password_hash_by_client_id(client_id)

    # Encrypted [Server-Client key] with [Client key]
    iv__c, encrypted_sc_aes_key__with_c = encrypt_aes_cbc(key=client_password_hash, salt=salt, data=sc_aes_key)
    print("sav1_2")
    print("sav2")
    # Encrypt [aes_key__sc] with the key [server_aes_key]
    # server_aes_key = an aes key of which belongs to the server
    server_aes_key = models.db["servers"].get_aes_key_by_server_id(server_id)
    iv__s, encrypted_aes_key__s = encrypt_aes_cbc(key=server_aes_key, salt=salt, data=aes_key__sc)
    print("sav3")
    timestamp = time.time()
    expiration_time = str(int(time.time() + 5 * 60)).encode('utf-8')  # Now + 5 minutes (seconds) & Pack the timestamp into bytes
    print("sav4")
    # Encrypt [expiration_time] with the key [server_aes_key] using the *same* IV as before
    _, encrypted_expiration_time__s = encrypt_aes_cbc(key=server_aes_key, salt=salt, data=expiration_time, iv=iv__s)
    print("sav5")
    response = {
        'header': {
            'version': __api_version__,
            'code': 1603,
        }, 'payload': {
            'client_id': client_id,
            'symmetric_key': {
                'iv': pack_key_base64(iv__c),
                'aes_key': pack_key_base64(encrypted_aes_key__c)
            },
            'ticket': {
                'version': __api_version__,
                'client_id': client_id,
                'server_id': server_id,
                'timestamp': timestamp,
                'ticket_iv': pack_key_base64(iv__s),
                'aes_key': pack_key_base64(encrypted_aes_key__s),
                'expiration_time': pack_key_base64(encrypted_expiration_time__s)
            }
        }
    }
    pack_and_send(connection, response)


def not_found_controller(connection, req):
    raise ValueError("Invalid request code")
