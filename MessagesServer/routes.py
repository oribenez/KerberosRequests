from controller import (send_symmetric_key,
                        send_message,
                        not_found_controller)

routes = {
    '1028': send_symmetric_key,
    '1029': send_message,
    '0': not_found_controller
}
