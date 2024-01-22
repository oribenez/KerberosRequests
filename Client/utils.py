import ipaddress


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
