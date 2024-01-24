import socket
import sys
import threading

import data
from api import register_new_server
from lib.ServerException import ServerException
from lib.config import package_dict
from routes import routes
from lib.utils import receive_data, unpack_data, REQUEST, send, RESPONSE, unpack_key_hex, unpack_key_base64
from config import (__api_version__,
                    __server_creds_filename__)
import config as cfg


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


def run_server():
    msg_server_ip, msg_server_port = data.db['server_info']['server_ip'], data.db['server_info']['server_port']
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((msg_server_ip, msg_server_port))
    server_socket.listen(10)  # Allow up to 10 queued connections

    print(f"Messages server is listening on port {msg_server_port}")

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


def read_server_creds_from_file(filename='msg.info'):
    try:
        with open(filename, "r") as file:
            lines = file.readlines()

            # Extracting information
            ip, port = lines[0].strip().split(':')

            if len(lines) >= 2:
                name = lines[1].strip()
            else:
                # ask from user the server name to register
                while True:
                    name = input("Please type server name: ") or 'Printer'  # FIXME: for testing only

                    if len(name) > 100:
                        print("Server name must be max 100 characters. ")
                    else:
                        break

            # Validate
            if not port.isdigit():
                raise ValueError("Invalid port number.")

            server_info = {
                'name': name,
                'server_ip': ip,
                'server_port': int(port),
            }

            if len(lines) >= 3:
                server_id = unpack_key_hex(lines[2].strip().encode('utf-8')).decode('utf-8')
                aes_key = unpack_key_base64(lines[3].strip().encode('utf-8'))
                server_info = {**server_info, **{'server_id': server_id, 'aes_key': aes_key}}

            return server_info

    except FileNotFoundError:
        print(f"Info: File '{filename}' not found.")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

    return None


def get_server_info_gui():
    server = read_server_creds_from_file(__server_creds_filename__)

    # register new client at KDC server
    if 'server_id' not in server:
        server = register_new_server(server)

    return server


def main():
    try:
        # load server info from file, if not exist, register new server
        server_info = get_server_info_gui()
        print(f"Server Info: {server_info}")

        # load database
        data.load_db(server_info_init=server_info)

        # read KDC server info file
        cfg.read_kdc_server_info()

        if server_info:
            run_server()
    except ServerException as se:
        print(se)


if __name__ == "__main__":
    main()
