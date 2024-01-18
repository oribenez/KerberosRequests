import ipaddress
import json
import socket


def read_user_from_file(filename):
    try:
        with open(filename, "r") as file:
            lines = file.readlines()

            # Extracting information
            ip, port = lines[0].strip().split(":")
            name = lines[1].strip()
            unique_ascii_key = lines[2].strip()

            # Validate
            if not port.isdigit():
                raise ValueError("Invalid port number.")
            # Validate IP address using the ipaddress module
            try:
                ipaddress.IPv4Address(ip)
            except ipaddress.AddressValueError:
                raise ValueError("Invalid IPv4 address.")

            return {
                'ip': ip, 'port': port, 'name': name, 'unique_ascii_key': unique_ascii_key
            }

    except FileNotFoundError:
        print(f"Info: File '{filename}' not found.")
    except ValueError as ve:
        print(f"Error: {str(ve)}")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

    return None


def send_request(ip, port, header, payload):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip, port))
    except ConnectionRefusedError:
        raise Exception("Error: Connection refused. Ensure that the server is running.")

    try:
        # Send message to server
        # {'EOF': 0} is a sign that this is the end of the request data for the buffer to receive
        msg_data = {'header': header, 'payload': payload} | {'EOF': 0}

        # Convert the dictionary to a JSON string and then send to server
        json_data = json.dumps(msg_data)
        client_socket.sendall(json_data.encode())

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
