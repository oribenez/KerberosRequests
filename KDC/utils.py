import json
import sys

from Crypto.Util import number
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


def hash_password(password):
    # Create a new SHA-256 hash object
    hasher = SHA256.new()

    # Update the hash object with the password
    hasher.update(password.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hashed_password = hasher.hexdigest()

    return hashed_password


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

def pack_and_send(connection, response):
    decorated_response = add_payload_size_to_header(response)
    json_response = json.dumps(decorated_response).encode()
    connection.sendall(json_response)