import json
import socket
import sys
import threading

from utils import read_port_from_file
from routes import routes


def handle_request(connection):
    try:
        # Receive request from client
        msg_data = receive_buffered_request(connection)

        req_header = msg_data['header'] or {}
        # req_payload = msg_data.get('payload', '')
        req_code = str(req_header['code']) or '0'

        controller = routes.get(req_code, '0')  # 0 means, not found
        controller(connection, msg_data)
        # print(f"Received from client: {msg_data}")

        # Response to client
        msg_send = b"Server received your message"
        connection.sendall(msg_send)

    except Exception as e:
        print(f"Error during communication: {e}")

    finally:
        connection.close()


def receive_buffered_request(connection, timeout=10):
    connection.settimeout(timeout)  # Set a timeout for this connection

    try:
        buffer = b''

        while True:
            data = connection.recv(1024)
            if not data:
                # Connection closed by the client
                break

            buffer += data

            if b'EOF' in buffer:
                break

        msg_receive = buffer.decode()
        msg_data = json.loads(msg_receive)

        return msg_data
    except:
        print("Error: Invalid JSON format")
        return None


def run_server():
    port = read_port_from_file()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', port))
    server_socket.listen(10)  # Allow up to 10 queued connections

    print(f"Server is listening on port {port}")

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


if __name__ == "__main__":
    run_server()
