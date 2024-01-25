from Client import data
from lib.ServerException import ServerException
# from config import __user_creds_filename__, read_kdc_server_info
import config as cfg
from lib.utils import color, GREEN, bold
from utils import read_user_from_file
from api import register_new_user, get_servers_list, send_message


def get_client_info_gui():
    client = read_user_from_file(cfg.__user_creds_filename__)
    if not client:  # client file not found

        # ask from client to sign up
        while True:
            user_name = input("Please type your name: ") or 'Michael Jackson'  # FIXME: for testing only

            if len(user_name) > 100:
                print("Username must be max 100 characters. ")
            else:
                break

        user_pass = input("Please type password: ") or 'Avocado&Salt4Me'  # FIXME: for testing only

        # register new client at KDC server
        client = register_new_user(user_name, user_pass)

    return client


def choose_server_gui(client):
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

        server_index = server_choice_num - 1
        if 0 <= server_index < len(servers_list):
            break  # correct server index
        else:
            print("Invalid server number. Please try again...")

    selected_server = servers_list[server_index]
    return selected_server


def send_message_gui(client, server):
    print(f"Type the message you want to send \"{server['name']}\" [end-to-end encrypted]\n")
    message = input(color("Message:\n‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\n", GREEN))

    client_id = client["client_id"]
    client_password = input("Type your password: ") or 'Avocado&Salt4Me'  # FIXME: for testing only

    # send the message to the Messages server
    send_message(client_id, client_password, server, message)

    return False


def main():

    # GUI
    try:
        # read KDC server info file
        cfg.read_kdc_server_info()

        # load database
        data.load_db()

        # load client from file, if not exist, register new client
        client = get_client_info_gui()
        print(f"Client info: ", client)

        # ask client to choose a server to send a message.
        selected_server = choose_server_gui(client)

        while True:
            # ask client to write a message to send to the selected server.
            is_quit = send_message_gui(client, selected_server)

            if is_quit:
                break

    except ServerException as se:
        print(se)


if __name__ == "__main__":
    main()
