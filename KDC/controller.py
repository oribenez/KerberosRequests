import json
import time
from datetime import datetime, timedelta

from Crypto.Random import get_random_bytes

from config import __api_version__
from utils import generate_random_uuid, hash_password, pack_and_send, encrypt_aes_cbc
import KDC.db.models as models


def register_client(connection, req):
    try:
        # add client to clients list
        client_id = generate_random_uuid()
        password_hash = hash_password(req["payload"]["password"])
        now = datetime.now()
        formatted_timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
        client = {
            "client_id": client_id,
            "name": req["payload"]["name"],
            "password_hash": password_hash,
            "last_seen": formatted_timestamp
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
        response = {
            'header': {
                'version': __api_version__,
                'code': 1601,
            }
        }

    pack_and_send(connection, response)


def get_servers_list(connection, req):
    print("get_servers_list()")
    try:
        servers_list = models.db["servers"].get_all_servers()

        response = {
            'header': {
                'version': __api_version__,
                'code': 1602,
            }, 'payload': {
                'servers_list': servers_list
            }
        }

    except Exception as e:
        response = {
            'header': {
                'version': __api_version__,
                'code': 1609,
            }
        }

    pack_and_send(connection, response)


def get_symmetric_key(connection, req):
    print("get_symmetric_key()")
    try:
        # unpack request values
        client_id = req["header"]["client_id"]
        server_id = req["payload"]["server_id"]
        nonce = req["payload"]["nonce"]

        ## prepare response to client

        # Generate a random 256-bit (32-byte) AES key for server and client
        aes_key__sc = get_random_bytes(32)  # sc - aes key belongs to both the server and client

        # Encrypt [aes_key__sc] with the key [client_password_hash]
        # client_password_hash = a hash of the client password that he used at registration
        client_password_hash = models.db["clients"].get_password_hash_by_client_id(client_id)
        iv__c, encrypted_aes_key__c = encrypt_aes_cbc(key=client_password_hash, data=aes_key__sc)

        # Encrypt [aes_key__sc] with the key [server_aes_key]
        # server_aes_key = an aes key of which belongs to the server
        server_aes_key = models.db["servers"].get_aes_key_by_server_id(server_id)
        iv__s, encrypted_aes_key__s = encrypt_aes_cbc(key=server_aes_key, data=aes_key__sc)

        timestamp = datetime.now()
        expiration_time = timestamp + timedelta(minutes=5)

        # Encrypt [expiration_time] with the key [server_aes_key] using the *same* IV as before
        _, encrypted_expiration_time__s = encrypt_aes_cbc(key=server_aes_key, data=expiration_time, iv=iv__s)

        response = {
            'header': {
                'version': __api_version__,
                'code': 1603,
            }, 'payload': {
                'client_id': client_id,
                'symmetric_key': {
                    'iv': iv__c,
                    'aes_key': encrypted_aes_key__c
                },
                'ticket': {
                    'version': __api_version__,
                    'client_id': client_id,
                    'server_id': server_id,
                    'timestamp': timestamp,
                    'ticket_iv': iv__s,
                    'aes_key': encrypted_aes_key__s,
                    'expiration_time': encrypted_expiration_time__s
                }
            }
        }

    except Exception as e:
        response = {
            'header': {
                'version': __api_version__,
                'code': 1609,
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
        response = {
            'header': {
                'version': __api_version__,
                'code': 1601,
            }
        }

    pack_and_send(connection, response)


def not_found_controller(connection, req):
    raise ValueError("Invalid request code")
