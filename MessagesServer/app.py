import base64
import json
import socket
import sys
import threading

from Crypto.Random import get_random_bytes

from routes import routes
from utils import read_port_from_file, pack_and_send, read_server_creds_from_file, send_request
from config import (__api_version__,
                    __server_creds_filename__,
                    __kdc_server_ip__,
                    __kdc_server_port__,
                    __msg_server_port__)


def handle_request(connection):
    controller = 'undefined'
    try:
        # Receive request from client
        msg_data = receive_buffered_request(connection)

        req_header = msg_data['header'] or {}
        # req_payload = msg_data.get('payload', '')
        req_code = str(req_header['code']) or '0'

        controller = routes.get(req_code, '0')  # 0 means, not found
        controller(connection, msg_data)

    except Exception as e:
        print(f"Exception in function: {controller.__name__ or controller}")
        print(f"Error during communication: {e}")

        # Response to client in case of error
        err_response = {
            'header': {
                'version': __api_version__,
                'code': 1609
            }
        }

        pack_and_send(connection, err_response)

    finally:
        connection.close()


def receive_buffered_request(connection, timeout=10):
    connection.settimeout(timeout)  # Set a timeout for this connection

    try:
        data = b''

        while True:
            chunk = connection.recv(1024)
            if not chunk:
                # Connection closed by the client
                break

            data += chunk

            if b'"EOF": 0}' in chunk:  # signature of End Of File - EOF
                break

        msg_receive = data.decode()
        msg_data = json.loads(msg_receive)

        return msg_data

    except json.JSONDecodeError as e:
        print("Error: Invalid JSON format")
    except Exception as e:
        print("Error")

    return None


def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', __msg_server_port__))
    server_socket.listen(10)  # Allow up to 10 queued connections

    print(f"Messages server is listening on port {__msg_server_port__}")

    try:
        while True:
            connection, address = server_socket.accept()
            print(f"Connection established from {address}")

            # Start a new thread to handle the client
            client_handler = threading.Thread(target=handle_request, args=[connection])
            client_handler.start()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
        server_socket.close()
        sys.exit()


def register_new_server():
    # ask from user the username and password to register
    while True:
        server_name = input("Please type server name: ") or 'Printer'  # FIXME: for testing only

        if len(server_name) > 100:
            print("Server name must be max 100 characters. ")
        else:
            break

    # Generate a random 256-bit (32-byte) AES key for server and client
    aes_key = get_random_bytes(32)
    base64_aes_key = base64.b64encode(aes_key).decode('utf-8')

    # request to server - new connection
    req_header = {
        'client_id': 'undefined',
        'version': 24,
        'code': 1027
    }
    req_payload = {
        'name': server_name,
        'aes_key': base64_aes_key
    }

    try:
        response = send_request(__kdc_server_ip__, __kdc_server_port__, req_header, req_payload)
        print("response: ", response)  # FIXME: TESTING

        response_code = response["header"]["code"]
        if response_code == 1600:  # registration success
            print("[1600] Registration success")
            # save user to file
            with open(__server_creds_filename__, "w") as file:
                server_id = response["payload"]["server_id"]
                file.write(f"{__msg_server_port__}\n{server_name}\n{server_id}\n{base64_aes_key}")

            return True
        elif response_code == 1601:  # registration failed
            print("[1601] Registration failed")
        else:  # unknown response
            print("Unknown response from server: ", response)

    except Exception as e:
        print(e)

    return False


if __name__ == "__main__":
    creds = read_server_creds_from_file(__server_creds_filename__)
    if creds:  # file found
        server_exist = True
    else:  # file not found
        # register new server
        server_exist = register_new_server()

    if server_exist:
        run_server()
