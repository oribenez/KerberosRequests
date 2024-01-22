from utils import read_port_from_file

__api_version__ = 24
__server_creds_filename__ = 'msg.info'

__kdc_server_ip__ = '127.0.0.1'
__kdc_server_port__ = read_port_from_file() or 8000

__msg_server_ip__ = '127.0.0.1'
__msg_server_port__ = __kdc_server_port__ + 1 or 8001
