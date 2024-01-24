import socket
import sys
import threading

import data
from api import register_new_server
from lib.ServerException import ServerException
from lib.config import package_dict
from routes import routes
from utils import read_server_creds_from_file
from lib.utils import receive_data, unpack_data, REQUEST, send, RESPONSE
from config import (__api_version__,
                    __server_creds_filename__,
                    __msg_server_port__,
                    __msg_server_ip__)


def handle_request(connection):
    controller = 'undefined'
    try:
        # Receive request from client
        data_receive = receive_data(connection)
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


def run_server(server_info):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((__msg_server_ip__, __msg_server_port__))
    server_socket.listen(10)  # Allow up to 10 queued connections

    print(f"Messages server is listening on port {__msg_server_port__}")

    try:
        # load database
        data.load_db(server_info_init=server_info)

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


def get_server_info_gui():
    server = read_server_creds_from_file(__server_creds_filename__)
    if not server:  # client file not found

        # ask from user the server name to register
        while True:
            server_name = input("Please type server name: ") or 'Printer'  # FIXME: for testing only

            if len(server_name) > 100:
                print("Server name must be max 100 characters. ")
            else:
                break

        # register new client at KDC server
        server = register_new_server(server_name)

    return server


def main():
    try:
        # load server info from file, if not exist, register new server
        server_info = get_server_info_gui()

        if server_info:
            run_server(server_info)
    except ServerException as se:
        print(se)


if __name__ == "__main__":
    main()
