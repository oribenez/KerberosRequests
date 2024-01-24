import time

from MessagesServer.utils import are_timestamps_close
from lib.utils import decrypt_aes_cbc, unpack_key_base64, pack_key_base64, send, RESPONSE, color, GREEN
from config import __api_version__
from lib.ServerException import ServerException
import data as data


def accept_symmetric_key(connection, req):
    print(color('accept_symmetric_key()', GREEN))
    server_info = data.db["server_info"]
    server_aes_key = server_info["aes_key"]

    authenticator = req['payload']['authenticator']
    ticket = req['payload']['ticket']
    print("authenticator: ", authenticator)
    print("ticket: ", ticket)

    # Ticket
    ticket_version = int(ticket['version'])
    ticket_client_id = ticket['client_id']
    ticket_server_id = ticket['server_id']
    ticket_timestamp = float(ticket['timestamp'])
    ticket_iv = ticket['ticket_iv']
    ticket_aes_key = decrypt_aes_cbc(server_aes_key, ticket_iv, ticket['aes_key'])
    ticket_expiration_time = float(decrypt_aes_cbc(server_aes_key, ticket_iv, ticket['expiration_time']).decode('utf-8'))

    # Authenticator
    auth_iv = authenticator['auth_iv']
    auth_version = int(decrypt_aes_cbc(ticket_aes_key, auth_iv, authenticator['version']).decode('utf-8'))
    auth_client_id = decrypt_aes_cbc(ticket_aes_key, auth_iv, authenticator['client_id']).decode('utf-8')
    auth_server_id = decrypt_aes_cbc(ticket_aes_key, auth_iv, authenticator['server_id']).decode('utf-8')
    auth_timestamp = float(decrypt_aes_cbc(ticket_aes_key, auth_iv, authenticator['timestamp']).decode('utf-8'))

    # Validation: Ticket info match the Auth info
    if auth_version != ticket_version or \
            auth_client_id != ticket_client_id or \
            auth_server_id != ticket_server_id or \
            not are_timestamps_close(auth_timestamp, ticket_timestamp, 200):
        print(auth_version, ticket_version)
        print(auth_client_id, ticket_client_id)
        print(auth_server_id, ticket_server_id)
        print(auth_timestamp, ticket_timestamp, are_timestamps_close(auth_timestamp, ticket_timestamp, 30)) # FIXME: 1705871910.606503 1705871909.9221919 they are different!!
        print('invalid ticket')
        raise ServerException()

    # Validation: check that ticket has not expired
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
    send(connection, RESPONSE, response)
    print('[SUCCESS] Symmetric key accepted')


def send_message(connection, req):
    client_id = req['header']['client_id']
    aes_key = data.db['tickets'].get_aes_key(client_id)
    iv = req['payload']['iv']
    encrypted_message = req['payload']['message_content']  # FIXME: problem with unpacking the last var, it is unpacking only 1 byte
    print('encrypted_message: ', encrypted_message)
    message = decrypt_aes_cbc(aes_key, iv, encrypted_message).decode('utf-8')

    print("Message received: ", message)

    response = {
        'header': {
            'version': __api_version__,
            'code': 1605
        }
    }
    send(connection, RESPONSE, response)


def not_found_controller(connection, req):
    raise ValueError("Invalid request code")
