import secrets
import sys
import time

from Crypto.Random import get_random_bytes

from Client import data
from lib.ServerException import ServerException
from lib.utils import send_request, hash_password, decrypt_aes_cbc, \
    encrypt_aes_cbc, color, GREEN
import Client.config as cfg
from lib.config import __api_version__
from lib.config import salt


def register_new_user(user_name, user_pass):
    """
        Registers a new user with the Key Distribution Center (KDC) server.
        the function also saves the user information to a long storage file, me.info .

        Params:
        - user_name (str): The desired username for the new user.
        - user_pass (str): The password for the new user.

        Returns:
        - dict: Client information, including 'name' and 'client_id'.

        Raises:
        - ServerException: Raised in case of errors during the registration process.
        """

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

    response = send_request(cfg.__kdc_server_ip__, cfg.__kdc_server_port__, request)

    response_code = response["header"]["code"]
    if response_code == 1600:  # registration success
        print("[Success] Client registered")
        # save user to file
        with open(cfg.__user_creds_filename__, "w") as file:
            client_id = response["payload"]["client_id"]
            file.write(f"{user_name}\n{client_id}")

        client = {
            'name': user_name, 'client_id': client_id
        }

        return client

    elif response_code == 1601:  # registration failed
        print("[Fail] Registration failed")
        raise ServerException()

    else:  # unknown response
        print("Unknown response from server: ", response)
        raise ServerException()


def get_servers_list(client):
    # print('get_servers_list()')
    request = {
        'header': {
            'client_id': client["client_id"],
            'version': __api_version__,
            'code': 1026
        }
    }
    response = send_request(cfg.__kdc_server_ip__, cfg.__kdc_server_port__, request)

    # expecting a list in payload
    servers_list = response['payload']

    return servers_list


def get_symmetric_key_kdc(client_id: str, client_password: str, server_id: str) -> tuple:
    """
        Requests a symmetric key from the Key Distribution Center (KDC) for secure communication with a specified server.

        Params:
        - client_id (str): The client's unique identifier.
        - client_password (str): The client's password.
        - server_id (str): The server's unique identifier.

        Returns:
        - tuple: A tuple containing the initialization vector (iv), decrypted session AES key, and the received ticket.

        Raises:
        - ServerException: Raised in case of errors during the key exchange process.
        """

    # Generate a random nonce (8 bytes)
    nonce = get_random_bytes(8)

    request = {
        'header': {
            'client_id': client_id,
            'version': __api_version__,
            'code': 1027
        },
        'payload': {
            'server_id': server_id,
            'nonce': nonce
        }
    }

    response = send_request(cfg.__kdc_server_ip__, cfg.__kdc_server_port__, request)
    if response['header']['code'] != 1603:
        raise ServerException()

    symmetric_key = response['payload']['symmetric_key']
    iv = symmetric_key['symm_iv']
    encrypted_session_aes_key = symmetric_key['aes_key']
    encrypted_nonce = symmetric_key['nonce']

    client_password_hash = hash_password(client_password, salt)
    decrypted_session_aes_key = decrypt_aes_cbc(client_password_hash, iv, encrypted_session_aes_key)
    decrypted_nonce = decrypt_aes_cbc(client_password_hash, iv, encrypted_nonce)

    # Check if nonces are different
    if nonce != decrypted_nonce:
        raise ServerException()

    ticket = response['payload']['ticket']

    return iv, decrypted_session_aes_key, ticket


def send_symmetric_key_msg_server(client_id, server_info, session_aes_key, ticket):
    """
        Sends the symmetric key and authentication details to a specified Messaging server for secure communication.

        Params:
        - client_id (str): The client's unique identifier.
        - server_info (dict): Information about the target server, including 'server_id', 'server_ip', and 'server_port'.
        - session_aes_key (bytes): The session AES key used for encryption.
        - ticket (dict): The ticket received from the Key Distribution Center (KDC).

        Raises:
        - ServerException: Raised if the server does not accept the symmetric key.
        """

    server_id, server_ip, server_port = server_info["server_id"], server_info["server_ip"], server_info["server_port"]

    timestamp = str(time.time())
    iv, encrypted_version__with_session_key = encrypt_aes_cbc(key=session_aes_key,
                                                              data=str(__api_version__).encode('utf-8'))
    _, encrypted_client_id__with_session_key = encrypt_aes_cbc(key=session_aes_key, data=client_id.encode('utf-8'),
                                                               iv=iv)
    _, encrypted_server_id__with_session_key = encrypt_aes_cbc(key=session_aes_key, data=server_id.encode('utf-8'),
                                                               iv=iv)
    _, encrypted_timestamp__with_session_key = encrypt_aes_cbc(key=session_aes_key, data=timestamp.encode('utf-8'),
                                                               iv=iv)

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

    response = send_request(server_ip, server_port, request)

    # Make sure the server accepted the symmetric key
    if response["header"]["code"] != 1604:
        raise ServerException()


def send_message(client_id, client_password, server_info, message):
    """
        Sends an end-to-end encrypted message to a specified Messaging server.

        Params:
        - client_id (str): The client's unique identifier.
        - client_password (str): The client's password.
        - server_info (dict): Information about the target server, including 'server_id', 'server_ip', and 'server_port'.
        - message (str): The message to be sent.

        Raises:
        - ServerException: Raised if there are issues with the message delivery process.
        """

    try:
        server_id, server_ip, server_port = server_info["server_id"], server_info["server_ip"], server_info["server_port"]

        # Resend message if ticket is invalid or server error
        resend_amount_if_fails = 2
        is_resend = False
        for i in range(resend_amount_if_fails):

            key = data.db['keys'].get_key_by_server_id(server_id)
            if key is None or is_resend:
                # get a new ticket and send it to the MSG server
                iv, aes_key, ticket = get_symmetric_key_kdc(client_id, client_password, server_id)
                send_symmetric_key_msg_server(client_id, server_info, aes_key, ticket)

                # add key to keys db
                key = {
                    'iv': iv,
                    'aes_key': aes_key,
                    'server_id': server_id
                }
                data.db['keys'].add_key(key)
            else:
                iv, aes_key = key['iv'], key['aes_key']

            # Encrypt [Message] with [Session key]
            _, encrypted_message = encrypt_aes_cbc(aes_key, message.encode('utf-8'), iv)

            message_size = sys.getsizeof(encrypted_message)
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
            response = send_request(server_ip, server_port, request)

            if response['header']['code'] == 1605:
                print(color('[SUCCESS] Message sent and received by MSG server', GREEN))
                break

            is_resend = True
    except Exception:
        raise ServerException()

