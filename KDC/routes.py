from controller import (register_client,
                        get_servers_list,
                        register_server,
                        get_symmetric_key,
                        not_found_controller)

routes = {
    '1025': register_client,
    '1026': get_servers_list,
    '1027': register_server,
    '1028': get_symmetric_key, # FIXME: the code is not correct need to ask Yizhak
    '0': not_found_controller
}
