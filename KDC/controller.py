def register_client(connection, msg_data):
    print("register_client()")


def get_servers_list(connection, msg_data):
    print("get_servers_list()")


def get_symmetric_key(connection, msg_data):
    print("get_symmetric_key()")


def register_server(connection, msg_data):
    print("register_server()")


def not_found_controller(connection, msg_data):
    raise ValueError("Invalid request code")
