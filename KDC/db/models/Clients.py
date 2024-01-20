import os
import threading

from KDC.db.models.RecordAlreadyExist import RecordAlreadyExist


class Clients:

    def __init__(self, file_path='/db/data/clients'):
        self.clients = []
        self.lock = threading.Lock()
        self.file_path = file_path

        self.load_clients_from_file()

    def load_clients_from_file(self):
        with self.lock:
            clients_temp = []

            try:
                with open(os.getcwd()+self.file_path, 'r') as file:

                    for line in file:
                        client_data = line.strip().split(':')
                        if len(client_data) == 4:
                            client = {
                                'client_id': client_data[0],
                                'name': client_data[1],
                                'password_hash': client_data[2],
                                'last_seen': client_data[3]
                            }
                            clients_temp.append(client)

                    self.clients = list(clients_temp)  # shallow copy
            except (FileNotFoundError, IOError):
                print(f"Error: Unable to load clients from file '{self.file_path}'")

    def save_clients_to_file(self):
        try:
            with open(os.getcwd()+self.file_path, 'w') as file:
                for client in self.clients:
                    file.write(f"{client['client_id']}:{client['name']}:{client['password_hash']}:{client['last_seen']}\n")
        except IOError:
            print(f"Error: Unable to save clients to file '{self.file_path}'")

    def is_exist(self, other_client):
        is_exist = False
        for client in self.clients:
            if client["name"] == other_client["name"]:
                is_exist = True
                break
                
        return is_exist

    def get_password_hash_by_client_id(self, client_id):
        print(f"get_password_hash_by_client_id(client_id={client_id})")
        print(self.clients)
        for client in self.clients:
            if client["client_id"] == client_id:
                return client["password_hash"]

    def add_client(self, client):
        with self.lock:
            # check if client already exist by name
            if self.is_exist(client):
                err_msg = "Client already exist"
                print(err_msg)
                raise RecordAlreadyExist(err_msg)
            else:
                self.clients.append(client)
                self.save_clients_to_file()

