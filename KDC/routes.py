from controller import (register_client,
                        get_servers_list,
                        register_server,
                        get_symmetric_key,
                        not_found_controller)

routes = {
    '1024': register_client,
    '1025': register_server,
    '1026': get_servers_list,
    '1027': get_symmetric_key,
    '0': not_found_controller
}
