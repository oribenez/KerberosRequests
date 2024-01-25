import ipaddress

__api_version__ = 24
__server_creds_filename__ = 'msg.info'  # default

__kdc_server_ip__ = '127.0.0.1'  # default
__kdc_server_port__ = 8000  # default


def read_kdc_server_info(kdc_server_filename='srv.info'):
    """
    Reads the KDC server information (IP address and port) from a file.

    This function reads the KDC server information from the specified file and sets the global variables
    __kdc_server_ip__ and __kdc_server_port__ with the obtained values.

    Args:
        kdc_server_filename (str): The filename containing KDC server information. Defaults to 'srv.info'.

    Raises:
        ValueError: If the file contains an invalid port number or an invalid IPv4 address.
    """

    with open(kdc_server_filename, 'r') as file:
        ip, port = file.read().strip().split(':')
        try:
            port = int(port)
        except Exception:
            raise ValueError("Invalid port number.")

        # Validate IP address using the ipaddress module
        try:
            ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError:
            raise ValueError("Invalid IPv4 address.")

        global __kdc_server_ip__, __kdc_server_port__
        __kdc_server_ip__, __kdc_server_port__ = ip, port
