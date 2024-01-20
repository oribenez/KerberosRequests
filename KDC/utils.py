import base64
import binascii
import hashlib
import hmac
import json
import sys

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util import number
from Crypto.Util.Padding import pad
from Crypto.Util.number import getPrime
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import uuid


def generate_random_uuid():
    # Generate a random integer to use as the UUID
    random_integer = number.getRandomNBitInteger(128)

    # Convert the integer to a bytes object
    uuid_bytes = random_integer.to_bytes(16, byteorder='little')

    # Create a UUID object from the bytes and convert it to a hex string without dashes
    uuid_without_dashes = str(uuid.UUID(bytes=uuid_bytes)).replace('-', '')

    return uuid_without_dashes


def hash_password_hex(password, salt, key_length=32, iterations=1000000):
    hashed_password = PBKDF2(password, salt, dkLen=key_length, count=iterations)
    hashed_password_hex = binascii.hexlify(hashed_password).decode('utf-8')
    return hashed_password_hex


def encrypt_aes_cbc(key, salt, data, iv=None):
    print("encrypt_aes_cbc(key, salt, data, iv=None):")

    if iv is None:
        iv = get_random_bytes(16)

    bf_key = PBKDF2(key, salt, dkLen=32, count=1000000)
    print(f"0: {key, data, iv}")
    cipher = AES.new(bf_key, AES.MODE_CBC, iv)
    print("1")
    ciphered_data = cipher.encrypt(pad(data, AES.block_size))
    print("2")

    return cipher.iv, ciphered_data


def pack_key_base64(key):
    return base64.b64encode(key).decode('utf-8')


def unpack_key_base64(key):
    return base64.b64decode(key)


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
