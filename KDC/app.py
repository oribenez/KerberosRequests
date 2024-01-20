import json
import socket
import sys
import threading

from utils import read_port_from_file, pack_and_send
from routes import routes
from config import __api_version__
import KDC.db.models as models


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

            if b'"EOF": 0}' or b"'EOF': 0}" in chunk:  # signature of End Of File - EOF
                break

        msg_receive = data.decode()
        msg_data = json.loads(msg_receive)

        return msg_data

    except json.JSONDecodeError as e:
        print("Error: Invalid JSON format")
    except Exception as e:
        print("Error: ", e)

    return None


def run_server():
    port = read_port_from_file()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', port))
    server_socket.listen(10)  # Allow up to 10 queued connections

    print(f"KDC server is listening on port {port}")

    try:
        # load database models
        models.load_db()

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


if __name__ == "__main__":
    run_server()
