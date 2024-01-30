from Client import data
from lib.ServerException import ServerException
# from config import __user_creds_filename__, read_kdc_server_info
import config as cfg
from lib.utils import color, GREEN, bold, RED, CYAN
from utils import read_user_from_file
from api import register_new_user, get_servers_list, send_message


def get_client_info_gui() -> dict:
    """
        Retrieves client information from a stored file or prompts the user to sign up and registers the new client.

        Returns:
        - dict: Client information, including 'user_id' and 'user_password'.
        """

    client = read_user_from_file(cfg.__user_creds_filename__)
    if not client:  # client file not found

        # ask from client to sign up
        while True:
            user_name = input("Please type your name: ") or 'Michael Jackson'  # FIXME: for testing only

            if len(user_name) > 255:
                print("Username must be max 255 characters. ")
            else:
                break

        user_pass = input("Please type password: ") or 'Avocado&Salt4Me'  # FIXME: for testing only

        # register new client at KDC server
        client = register_new_user(user_name, user_pass)

    return client


def choose_server_gui(client: dict) -> dict:
    """
        Allows the user to choose a server from the list obtained from the Key Distribution Center (KDC).

        Params:
        - client (dict): Contains client information.

        Returns:
        - dict: Information about the selected server, including 'name' and 'server_id'.
        """

    # get servers list from KDC
    servers_list = get_servers_list(client)

    print(color("\nServers List:\n‾‾‾‾‾‾‾‾‾‾‾‾‾", GREEN))

    for i, server in enumerate(servers_list):
        print(f"{i + 1}) {bold('Server Name:')} {server['name']}, {bold('Server ID:')} {server['server_id']}")

    while True:
        server_choice_num = -1
        try:
            server_choice_num = int(input("Type server number (1,2,... ): "))
        except Exception as e:
            print("Invalid server number. Please try again...")
            continue

        server_index = server_choice_num - 1
        if 0 <= server_index < len(servers_list):
            break  # correct server index
        else:
            print("Invalid server number. Please try again...")

    selected_server = servers_list[server_index]
    return selected_server


def send_message_gui(client: dict, server: dict) -> bool:
    """
        Sends an encrypted message to the specified server using Kerberos.

        Params:
        - client (dict): Contains client info.
        - server (dict): Contains server info.

        Returns:
        - bool: False.
        """
    print(f"Type the message you want to send \"{server['name']}\" [end-to-end encrypted]\n")
    message = input(color("Message: ", GREEN) + "(type ':q' to return to servers list)\n" + color("‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\n", GREEN))

    if message == ':q':
        return True
    elif message == '':
        return False

    client_id = client["client_id"]
    if 'client_password' in data.db:
        client_password = data.db['client_password']
    else:
        client_password = input("Type your password: ") or 'Avocado&Salt4Me'  # FIXME: for testing only

        # save client's password to not ask him each time he sends a message
        data.db['client_password'] = client_password

    try:
        # send the message to the Messages server
        send_message(client_id, client_password, server, message)
    except Exception as e:
        # delete the password since it is maybe the problem for the issue
        # maybe the user typed a wrong password
        del data.db['client_password']
        print(color('Maybe the password you\'ve entered is wrong, or the problem is with the Messaging server.', CYAN))
        raise e

    return False


def main():
    """
        Main function to run the messaging application with a graphical user interface (GUI).

        The function performs the following steps:
        1. Reads Key Distribution Center (KDC) server information from a file.
        2. Loads the database.
        3. Retrieves client information from a stored file or prompts the user to sign up and registers the new client.
        4. Asks the user to choose a server and sends end-to-end encrypted messages until the user decides to quit and choose a different server.

        Exceptions:
        - ServerException: Raised in case of errors related to server operations.

        Note:
        - The application provides a menu-driven interface for users to interact with the messaging system.
        """

    # GUI
    max_try = 3
    for i in range(max_try):
        try:
            # read KDC server info file
            cfg.read_kdc_server_info()

            # load database
            data.load_db()

            # load client from file, if not exist, register new client
            client = get_client_info_gui()
            print(f"Client info: ", client)

            break
        except ServerException as se:
            print(color(str(se), RED))

    while True:
        try:
            # ask client to choose a server to send a message.
            selected_server = choose_server_gui(client)

            while True:
                # ask client to write a message to send to the selected server.
                is_quit = send_message_gui(client, selected_server)

                # if the user type the message ':q' then it will return to menu to choose server
                if is_quit:
                    break
        except ServerException as se:
            print(color(str(se), RED))


if __name__ == "__main__":
    main()
