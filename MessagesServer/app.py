import socket
import sys
import threading

import data
from api import register_new_server
from lib.ServerException import ServerException
from lib.config import package_dict
from routes import routes
from lib.utils import receive_data, unpack_data, REQUEST, send, RESPONSE, unpack_key_hex, unpack_key_base64, color, RED
from config import (__api_version__,
                    __server_creds_filename__)
import config as cfg


def handle_request(connection):
    """
    Handles the incoming requests from clients.

    This function receives a request from the client, determines the appropriate controller based on the request code,
    and then executes the corresponding controller to process the request.

    Args:
        connection (socket): The connection socket for communication with the client.
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
    Runs the Messages server.

    This function binds the server socket to the specified IP address and port, listens for incoming connections,
    and starts a new thread to handle each client.

    Note: The server socket is bound to the IP and port specified in the 'server_info' stored in the 'data.db'.
    """
    msg_server_ip, msg_server_port = data.db['server_info']['server_ip'], data.db['server_info']['server_port']
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((msg_server_ip, msg_server_port))
    server_socket.listen(10)  # Allow up to 10 queued connections

    print(f"Messages server is listening on port {msg_server_port}")

    try:

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


def read_server_creds_from_file(filename='msg.info'):
    """
    Reads server information from a file.

    Args:
        filename (str): The name of the file to read server information from.

    Returns:
        dict: Server information including 'name', 'server_ip', 'server_port', 'server_id', and 'aes_key'.
              Returns None if there is an issue reading the file or extracting information.
    """
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
                    name = input("Please type server name: ").strip()

                    if len(name) > 255:
                        print("Server name must be max 255 characters. ")
                    elif len(name) == 0:
                        print("Please type server name. ")
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
    """
    Gets server information, reads it from a file, and registers a new server if necessary.

    Returns:
        dict: Server information including 'server_id', 'name', 'server_ip', 'server_port', and 'aes_key'.
    """
    server = read_server_creds_from_file(__server_creds_filename__)

    # register new client at KDC server
    if 'server_id' not in server:
        server = register_new_server(server)

    return server


def main():
    """
    Main function for running the server.

    - Loads server information from a file. If the file does not exist, registers a new server.
    - Loads the database.
    - Reads Key Distribution Center (KDC) server information from a file.
    - Runs the server.

    Raises:
        ServerException: If there is an issue with server registration.
    """
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
        print(color(str(se), RED))
    except KeyboardInterrupt:
        print("\nBye Bye...")
        sys.exit()


if __name__ == "__main__":
    main()
