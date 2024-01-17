

from utils import read_user_from_file, send_request

__user_creds_filename__ = 'me.info'
__auth_server_ip__ = '127.0.0.1'
__auth_server_port__ = 8000


def register_new_user():
    # ask from user the username and password to register
    while True:
        user_name = input("Please type your name: ") or 'Michael Jackson'  # FIXME: for testing only

        if len(user_name) > 100:
            print("Username must be max 100 characters. ")
        else:
            break

    user_pass = input("Please type password: ") or 'Avocado&Salt4Me'  # FIXME: for testing only

    # request to server - new connection
    req_header = {
        'client_id': 'undefined',
        'version': 24,
        'code': 1025
    }
    req_payload = {
        'name': user_name,
        'password': user_pass
    }

    response = send_request(__auth_server_ip__, __auth_server_port__, req_header, req_payload)
    print("response: ", response)  # FIXME: TESTING

    response_code = response["header"]["code"]
    if response_code == 1600:  # registration success
        print("[1600] Registration success")
        # save user to file
        with open(__user_creds_filename__, "w") as file:
            client_id = response["payload"]["client_id"]
            file.write(f"{__auth_server_ip__}:{__auth_server_port__}\n{user_name}\n{client_id}")

    elif response_code == 1601:  # registration failed
        print("[1601] Registration failed")

    else:  # unknown response
        print("Unknown response from server: ", response)


def main():

    user = read_user_from_file(__user_creds_filename__)

    if user:  # me.info file exists
        # TODO: request to server - connect again
        print(user)

    else:  # user file not found
        register_new_user()


if __name__ == "__main__":
    main()
