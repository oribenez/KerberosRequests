import json
import socket
import sys


def add_payload_size_to_header(request):
    payload = request.get("payload", {})
    payload_size = 0  # size in bytes
    if payload != {}:
        payload_size = sys.getsizeof(payload)

    new_request = {
        "header": request["header"] | {"payload_size": payload_size},
    }

    # add payload only if exist
    if payload_size != 0:
        new_request = new_request | {"payload": request["payload"]}

    return new_request


def pack_and_send(connection, response):
    decorated_response = add_payload_size_to_header(response)
    json_response = json.dumps(decorated_response).encode()
    connection.sendall(json_response)


def read_port_from_file(port_filename="port.info"):
    default_port = 1256  # default port

    try:
        with open(port_filename, "r") as port_file:
            port_file_txt = port_file.read().strip()

            # Validate
            port = int(port_file_txt)
            if 1 <= port <= 65535:
                return port
            else:
                print("Error: Port number must be between 1 and 65535.")

    except FileNotFoundError:
        print(f"Error: File '{port_filename}' not found.")
    except ValueError:
        print(f"Error: Invalid port number in '{port_filename}'.")

    print(f"Using default port: {default_port}")
    return default_port


def send_request(ip, port, header, payload):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.connect((ip, port))
    except ConnectionRefusedError:
        raise Exception("Error: Connection refused. Ensure that the server is running.")

    try:
        # Send message to server
        # {'EOF': 0} is a sign that this is the end of the request data for the buffer to receive
        msg_data = {'header': header, 'payload': payload} | {'EOF': 0}

        # Convert the dictionary to a JSON string and then send to server
        json_data = json.dumps(msg_data)
        server_socket.sendall(json_data.encode())

        # Receive response from server and parse the JSON-formatted message
        msg_receive = server_socket.recv(1024)
        msg_data = json.loads(msg_receive.decode())

        return msg_data

    except json.JSONDecodeError:
        raise Exception("Error: Response from server invalid JSON format")
    except Exception as e:
        raise Exception(f"Error during communication: {e}")

    finally:
        server_socket.close()


def read_server_creds_from_file(filename):
    try:
        with open(filename, "r") as file:
            lines = file.readlines()

            # Extracting information
            kdc_port = lines[0].strip()
            name = lines[1].strip()
            unique_ascii_key = lines[2].strip()
            symmetric_key = lines[3].strip()

            # Validate
            if not kdc_port.isdigit():
                raise ValueError("Invalid port number.")

            return {
                'port': kdc_port, 'name': name, 'unique_ascii_key': unique_ascii_key, 'symmetric_key': symmetric_key
            }

    except FileNotFoundError:
        print(f"Info: File '{filename}' not found.")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

    return None
