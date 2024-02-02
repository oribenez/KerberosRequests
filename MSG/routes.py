from controller import (accept_symmetric_key,
                        send_message,
                        not_found_controller)

"""
This dictionary maps request codes to their corresponding handling functions.

Explanation:
    - '1028': accept_symmetric_key - Handles requests related to accepting symmetric keys.
    - '1029': send_message - Handles requests related to sending messages.
    - '0': not_found_controller - Handles cases where the request code is not recognized.

Note:
    - If a request code is not present in the dictionary, the '0' code is associated with the
      not_found_controller function, which raises a ValueError indicating an invalid request code.
"""
routes = {
    '1028': accept_symmetric_key,
    '1029': send_message,
    '0': not_found_controller
}
