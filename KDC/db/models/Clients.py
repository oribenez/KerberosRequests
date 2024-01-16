import threading


class Clients:

    def __init__(self, file_path='../data/clients'):
        self.clients = []
        self.lock = threading.Lock()
        self.file_path = file_path

        self.load_clients_from_file()

    def load_clients_from_file(self):
        with self.lock:
            clients_temp = []

            try:
                with open(self.file_path, 'r') as file:
                    for line in file:
                        client_data = line.strip().split(':')
                        if len(client_data) == 4:
                            client = {
                                'ID': client_data[0],
                                'Name': client_data[1],
                                'PasswordHash': client_data[2],
                                'LastSeen': client_data[3]
                            }
                            clients_temp.append(client)

                    self.clients = list(clients_temp)  # shallow copy
            except (FileNotFoundError, IOError):
                print(f"Error: Unable to load clients from file '{self.file_path}'")

    def save_clients_to_file(self):
        with self.lock:
            try:
                with open(self.file_path, 'w') as file:
                    for client in self.clients:
                        file.write(f"{client['ID']}:{client['Name']}:{client['PasswordHash']}:{client['LastSeen']}\n")
            except IOError:
                print(f"Error: Unable to save clients to file '{self.file_path}'")

    def add_client(self, client):
        with self.lock:
            # TODO: check if client already exist
            self.clients.append(client)
            self.save_clients_to_file()
