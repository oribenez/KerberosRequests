import time
from datetime import datetime

from MessagesServer.utils import are_timestamps_close
from lib.utils import decrypt_aes_cbc, send, RESPONSE, color, GREEN, BLUE
from config import __api_version__
from lib.ServerException import ServerException
import data as data


def accept_symmetric_key(connection, req):
    """
    Handles the acceptance of a symmetric key from a client.

    This function performs the necessary validations and processes the symmetric key information received from the client.

    Args:
        connection (socket.socket): The connection socket to the client.
        req (dict): The request received from the client.

    Raises:
        ServerException: If there is an issue with the validation or if the ticket has expired.
    """

    server_info = data.db["server_info"]
    server_aes_key = server_info["aes_key"]

    authenticator = req['payload']['authenticator']
    ticket = req['payload']['ticket']

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
        print(auth_timestamp, ticket_timestamp, are_timestamps_close(auth_timestamp, ticket_timestamp, 200))
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
    print(color('[SUCCESS] Symmetric key accepted', GREEN))


def send_message(connection, req):
    """
    This function decrypts the received message using the client's AES key, prints the message to the screen with a
    timestamp, and sends an appropriate response back to the client.
    if the ticket already exist from previous relations then it will use it to decrypt the message (only if the ticket is not expired)

    Args:
        connection (socket.socket): The socket connection to the client.
        req (dict): The request received from the client.
    """

    client_id = req['header']['client_id']
    aes_key = data.db['tickets'].get_aes_key(client_id)
    if aes_key is not None:
        iv = req['payload']['iv']
        encrypted_message = req['payload']['message_content']

        # the decrypted message from client
        message = decrypt_aes_cbc(aes_key, iv, encrypted_message).decode('utf-8')

        # add time to message
        current_time = datetime.now()
        formatted_time = current_time.strftime("%H:%M")

        # print the message from the client to the screen with blue color
        print(color(f"Message received ({formatted_time}): {message}", BLUE))

        response = {
            'header': {
                'version': __api_version__,
                'code': 1605
            }
        }
    else:
        response = {
            'header': {
                'version': __api_version__,
                'code': 1609
            }
        }

    send(connection, RESPONSE, response)


def not_found_controller(connection, req):
    """
    Handles a request with an invalid code.

    Args:
        connection (socket.socket): The socket connection to the client.
        req (dict): The request received from the client.

    Raises:
        ValueError: Indicates that the request code is invalid.
    """
    raise ValueError("Invalid request code")
