import inspect
import json
import struct
import time
from datetime import datetime, timedelta

from Crypto.Random import get_random_bytes

from lib.config import salt
from config import __api_version__
from lib.utils import pack_key_hex, hash_password, encrypt_aes_cbc, pack_key_base64, unpack_key_hex, unpack_key_base64, \
    send, RESPONSE, color, RED, decrypt_aes_cbc, GREEN
from KDC.utils import generate_random_uuid
import db.models as models


def register_client(connection, req):
    """
    Registers a new client and adds them to the clients list.

    Params:
    - connection: The socket connection with the client.
    - req (dict): The request containing client information.

    Raises:
    - Exception: Raised in case of an error during client registration.

    Response:
    - Sends a response to the client indicating the success or failure of the registration.
    """

    try:
        # add client to clients list
        client_id = generate_random_uuid()
        name = req['payload']['name']
        password_hash = hash_password(req['payload']['password'], salt)
        timestamp = time.time()
        client = {
            "client_id": client_id,
            "name": name,
            "password_hash": password_hash,
            "last_seen": timestamp
        }
        # print('client: ', client)
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
        print(color('[SUCCESS] Client registered successfully', GREEN))

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
    """
    Registers a new server and adds it to the servers list.

    Params:
    - connection: The socket connection with the messaging server.
    - req (dict): The request containing server information.

    Raises:
    - Exception: Raised in case of an error during server registration.

    Response:
    - Sends a response to the client indicating the success or failure of the registration.
    """

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
        print(color('[SUCCESS] Server registered successfully', GREEN))

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
    """
    Retrieves the list of registered servers and sends it to the requesting client.

    Params:
    - connection: The socket connection with the client.
    - req (dict): The request for the servers list.

    Response:
    - Sends a response to the client containing the list of servers.
    """

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

    send(connection, RESPONSE, response)
    print(color('[SUCCESS] Servers list sent', GREEN))


def get_symmetric_key(connection, req):
    """
    Retrieves a symmetric key for secure communication between a client and a server.

    Params:
    - connection: The socket connection with the client.
    - req (dict): The request containing client id, server id, and a nonce.

    Response:
    - Sends a response to the client containing the symmetric key and a ticket for secure communication.
    """
    # unpack request values
    client_id = req["header"]["client_id"]
    server_id = req["payload"]["server_id"]
    nonce = req["payload"]["nonce"]  # TODO: handle nonce
    # # Prepare response to client
    # Generate AES key SHA-256
    session_aes_key = get_random_bytes(32)

    # client_password_hash - a hash of the client password that he used at registration
    client_password_hash = models.db["clients"].get_password_hash_by_client_id(client_id)

    # Encrypted [Nonce] with [Client key]
    iv__c, encrypted_nonce__with_c = encrypt_aes_cbc(key=client_password_hash, data=nonce)

    # Encrypted [Session key] with [Client key]
    _, encrypted_session_aes_key__with_c = encrypt_aes_cbc(key=client_password_hash, data=session_aes_key, iv=iv__c)

    # server AES key generated at server registration
    server_aes_key = models.db["servers"].get_aes_key_by_server_id(server_id)

    # Encrypted [Session key] with [Server key]
    ticket_iv, encrypted_session_aes_key__with_s = encrypt_aes_cbc(key=server_aes_key, data=session_aes_key)

    timestamp = time.time()
    expiration_time = str(int(time.time() + 5 * 60)).encode('utf-8')  # Now + 5 minutes (seconds) & Pack the timestamp into bytes

    # Encrypt [expiration_time] with the key [server_aes_key] using the *same* IV as before
    _, encrypted_expiration_time__with_s = encrypt_aes_cbc(key=server_aes_key, data=expiration_time, iv=ticket_iv)

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

    send(connection, RESPONSE, response)
    print(color('[SUCCESS] Symmetric key sent to client', GREEN))


def not_found_controller(connection, req):
    """
    Handles the case when the requested controller for a given request code is not found.

    Params:
    - connection: The socket connection with the client.
    - req (dict): The request with an invalid or unknown code.

    Raises:
    - ValueError: Raised to indicate an invalid request code.
    """
    raise ValueError("Invalid request code")
