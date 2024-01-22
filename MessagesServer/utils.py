from datetime import datetime

from lib.utils import unpack_key_hex, unpack_key_base64


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


def are_timestamps_close(timestamp1, timestamp2, threshold_seconds=1):
    # Convert timestamps to datetime objects
    dt1 = datetime.fromtimestamp(timestamp1)
    dt2 = datetime.fromtimestamp(timestamp2)

    # Calculate the absolute difference in seconds
    time_difference = abs((dt2 - dt1).total_seconds())

    # Check if the difference is within the threshold
    return time_difference <= threshold_seconds


def read_server_creds_from_file(filename):
    try:
        with open(filename, "r") as file:
            lines = file.readlines()

            # Extracting information
            port = lines[0].strip()
            name = lines[1].strip()
            server_id = unpack_key_hex(lines[2].strip().encode('utf-8')).decode('utf-8')
            aes_key = unpack_key_base64(lines[3].strip().encode('utf-8'))

            # Validate
            if not port.isdigit():
                raise ValueError("Invalid port number.")

            server_info = {
                'port': port, 'name': name, 'server_id': server_id, 'aes_key': aes_key
            }
            return server_info

    except FileNotFoundError:
        print(f"Info: File '{filename}' not found.")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

    return None
