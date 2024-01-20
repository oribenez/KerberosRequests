import base64
import binascii
import ipaddress
import json
import socket
import sys

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad


def read_user_from_file(filename):
    try:
        with open(filename, "r") as file:
            lines = file.readlines()

            # Extracting information
            ip, port = lines[0].strip().split(":")
            name = lines[1].strip()
            client_id = lines[2].strip()

            # Validate
            if not port.isdigit():
                raise ValueError("Invalid port number.")
            # Validate IP address using the ipaddress module
            try:
                ipaddress.IPv4Address(ip)
            except ipaddress.AddressValueError:
                raise ValueError("Invalid IPv4 address.")

            client = {
                'ip': ip, 'port': port, 'name': name, 'client_id': client_id
            }
            return client

    except FileNotFoundError:
        print(f"Info: File '{filename}' not found.")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

    return None


def pack_key_base64(key):
    return base64.b64encode(key).decode('utf-8')


def unpack_key_base64(key):
    return base64.b64decode(key)


def hash_password_hex(password, salt, key_length=32, iterations=1000000):
    hashed_password = PBKDF2(password, salt, dkLen=key_length, count=iterations)
    hashed_password_hex = binascii.hexlify(hashed_password).decode('utf-8')
    return hashed_password_hex


def decrypt_aes_cbc(key, iv, encrypted_data):

    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    deciphered_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

    return deciphered_data


def send_request(ip, port, req):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip, port))
    except ConnectionRefusedError:
        raise Exception("Error: Connection refused. Ensure that the server is running.")

    try:
        # Send message to server
        # {'EOF': 0} is a sign that this is the end of the request data for the buffer to receive
        msg_data = req | {'EOF': 0}

        # Convert the dictionary to a JSON string and then send to server
        pack_and_send(client_socket, msg_data)

        # Receive response from server and parse the JSON-formatted message
        msg_receive = client_socket.recv(1024)
        msg_data = json.loads(msg_receive.decode())

        return msg_data

    except json.JSONDecodeError:
        raise Exception("Error: Response from server invalid JSON format")
    except Exception as e:
        raise Exception(f"Error during communication: {e}")

    finally:
        client_socket.close()


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


# ANSI escape codes for some colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"


def color(text, color_code):
    return f"{color_code}{text}\033[0m"


def bold(text):
    return "\033[1m" + text + "\033[0m"