__user_creds_filename__ = 'me.info'

__kdc_server_ip__ = '127.0.0.1'
__kdc_server_port__ = 8000

__msg_server_ip__ = '127.0.0.1'
__msg_server_port__ = __kdc_server_port__ + 1 or 8001

import ipaddress


def read_kdc_server_info(kdc_server_filename='srv.info'):

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

