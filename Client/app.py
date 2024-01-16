import json
import socket


def main():
    port = 8000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect(('localhost', port))
    except ConnectionRefusedError:
        print("Error: Connection refused. Ensure that the server is running.")
        return

    try:
        header = {
            'client_id': 'undefined',
            'version': 24,
            'code': 1025
        }
        payload = "Sample Payload"

        # Send message to server
        # {'EOF': 0} is a sign that this is the end of the request data for the buffer to receive
        msg_data = {'header': header, 'payload': payload} | {'EOF': 0}

        # Convert the dictionary to a JSON string
        json_data = json.dumps(msg_data)
        client_socket.sendall(json_data.encode())

        # Receive response from server
        data = client_socket.recv(1024)
        print(f"Received from server: {data.decode()}")

    except Exception as e:
        print(f"Error during communication: {e}")

    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
