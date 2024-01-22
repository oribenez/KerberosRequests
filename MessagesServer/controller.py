import time

from MessagesServer.utils import are_timestamps_close
from lib.utils import pack_and_send, decrypt_aes_cbc, unpack_key_base64, pack_key_base64
from config import __api_version__
from lib.ServerException import ServerException
import data as data


def accept_symmetric_key(connection, req):
    server_info = data.db["server_info"]
    server_aes_key = server_info["aes_key"]

    authenticator = req['payload']['authenticator']
    ticket = req['payload']['ticket']

    # Ticket
    ticket_version = int(ticket['version'])
    ticket_client_id = ticket['client_id']
    ticket_server_id = ticket['server_id']
    ticket_timestamp = float(ticket['timestamp'])
    ticket_iv = unpack_key_base64(ticket['ticket_iv'])
    ticket_aes_key = decrypt_aes_cbc(server_aes_key, ticket_iv, unpack_key_base64(ticket['aes_key']))
    ticket_expiration_time = float(decrypt_aes_cbc(server_aes_key, ticket_iv, unpack_key_base64(ticket['expiration_time'])).decode('utf-8'))
    print("sav10")

    print("sav1")
    # Authenticator
    auth_iv = unpack_key_base64(authenticator['auth_iv'])
    # print("sav2")
    # try:
    #     print("server_aes_key: ", pack_key_base64(server_aes_key))
    #     print("auth_iv:", auth_iv)
    #     print("version:", authenticator['version'])
    #     print('---')
    #     print("client_id:", unpack_key_base64(authenticator['client_id']))
    # except Exception as e:
    #     print(e)

    auth_version = int(decrypt_aes_cbc(ticket_aes_key, auth_iv, unpack_key_base64(authenticator['version'])).decode('utf-8'))
    print("sav3")
    auth_client_id = decrypt_aes_cbc(ticket_aes_key, auth_iv, unpack_key_base64(authenticator['client_id'])).decode('utf-8')
    print("sav4")
    auth_server_id = decrypt_aes_cbc(ticket_aes_key, auth_iv, unpack_key_base64(authenticator['server_id'])).decode('utf-8')
    print("sav5")
    auth_timestamp = float(decrypt_aes_cbc(ticket_aes_key, auth_iv, unpack_key_base64(authenticator['timestamp'])).decode('utf-8'))
    print("sav6")

    # Validation: Ticket info match the Auth info
    if auth_version != ticket_version or \
            auth_client_id != ticket_client_id or \
            auth_server_id != ticket_server_id or \
            not are_timestamps_close(auth_timestamp, ticket_timestamp, 30):
        print(auth_version, ticket_version)
        print(auth_client_id, ticket_client_id)
        print(auth_server_id, ticket_server_id)
        print(auth_timestamp, ticket_timestamp, are_timestamps_close(auth_timestamp, ticket_timestamp, 30)) # FIXME: 1705871910.606503 1705871909.9221919 they are different!!
        print('invalid ticket')
        raise ServerException()

    # Validation: check that ticket has not expired
    print(ticket_expiration_time)
    current_time = time.time()
    if float(ticket_expiration_time) < current_time:
        print('ticket expired')
        raise ServerException()

    # add ticket to tickets cache
    decrypted_ticket = {
        'version': ticket_version,
        'client_id': ticket_client_id,
        'server_id': ticket_server_id,
        'timestamp': ticket_timestamp,
        'iv': ticket_iv,
        'aes_key': ticket_aes_key,
        'expiration_time': ticket_expiration_time
    }

    # Add ticket to tickets cache
    data.db["tickets"].add_ticket(decrypted_ticket)

    # response to client - Symmetric key accepted
    response = {
        'header': {
            'version': __api_version__,
            'code': 1604
        }
    }
    pack_and_send(connection, response)


def send_message(connection, req):
    client_id = req['header']['client_id']
    aes_key = data.db['tickets'].get_aes_key(client_id)
    iv = unpack_key_base64(req['payload']['iv'])
    encrypted_message = unpack_key_base64(req['payload']['message_content'])
    message = decrypt_aes_cbc(aes_key, iv, encrypted_message).decode('utf-8')

    print("Message received: ", message)

    response = {
        'header': {
            'version': __api_version__,
            'code': 1605
        }
    }
    pack_and_send(connection, response)


def not_found_controller(connection, req):
    raise ValueError("Invalid request code")
