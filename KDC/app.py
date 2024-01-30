import socket
import sys
import threading

from lib.config import package_dict
from lib.utils import receive_data, unpack_data, REQUEST, send, RESPONSE
from utils import read_port_from_file
from routes import routes
from config import __api_version__
import KDC.db.models as models


def handle_request(connection):
    """
        Handles incoming requests from clients and Messaging servers.

        Params:
        - connection: The socket connection with the client or the Messaging server.

        Raises:
        - Exception: Raised in case of an error during request processing.
        """

    controller = 'undefined'
    try:
        # Receive request from client
        data_receive = receive_data(connection, REQUEST)
        req = unpack_data(package_dict, REQUEST, data_receive)

        req_code = str(req['header']['code'])

        controller = routes.get(req_code, '0')  # 0 means, not found
        controller(connection, req)

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
        send(connection, RESPONSE, err_response)

    finally:
        connection.close()


def run_server():
    """
        Runs the Key Distribution Center (KDC) server, handling incoming connections.

        Raises:
        - KeyboardInterrupt: Raised when the server is manually interrupted, leading to a graceful shutdown.
        """

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
            # print(f"Connection established from {address}")

            # Start a new thread to handle the client
            client_handler = threading.Thread(target=handle_request, args=[connection])
            client_handler.start()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
        server_socket.close()
        sys.exit()


if __name__ == "__main__":
    run_server()
