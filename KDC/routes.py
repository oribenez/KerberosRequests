from controller import (register_client,
                        get_servers_list,
                        register_server,
                        get_symmetric_key,
                        not_found_controller)

"""
Routes dictionary for mapping request codes to corresponding controller functions.
- '1024': register_client - Handles client registration requests.
- '1025': register_server - Handles server registration requests.
- '1026': get_servers_list - Retrieves the list of registered servers.
- '1027': get_symmetric_key - Retrieves a symmetric key for secure communication.
- '0': not_found_controller - Handles invalid request codes.
"""

routes = {
    '1024': register_client,
    '1025': register_server,
    '1026': get_servers_list,
    '1027': get_symmetric_key,
    '0': not_found_controller
}
