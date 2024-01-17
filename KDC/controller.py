import json
import time
from datetime import datetime

from config import __api_version__
from utils import generate_random_uuid, hash_password, add_payload_size_to_header, pack_and_send
import KDC.db.models as models


def register_client(connection, msg_data):
    try:
        # add client to clients list
        client_id = generate_random_uuid()
        password_hash = hash_password(msg_data["payload"]["password"])
        now = datetime.now()
        formatted_timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
        client = {
            "client_id": client_id,
            "name": msg_data["payload"]["name"],
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


def get_servers_list(connection, msg_data):
    print("get_servers_list()")


def get_symmetric_key(connection, msg_data):
    print("get_symmetric_key()")


def register_server(connection, msg_data):
    print("register_server()")
    try:
        # response to client
        response = {
            'header': {
                'version': __api_version__,
                'code': 1600,
            }, 'payload': {
                'client_id': 0
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


def not_found_controller(connection, msg_data):
    raise ValueError("Invalid request code")
