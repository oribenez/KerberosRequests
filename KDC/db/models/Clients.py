import os
import threading

from KDC.db.models.RecordAlreadyExist import RecordAlreadyExist
from lib.utils import pack_key_hex, pack_key_base64, unpack_key_hex, unpack_key_base64


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
                                'client_id': unpack_key_hex(client_data[0].encode('utf-8')).decode('utf-8'),
                                'name': client_data[1],
                                'password_hash':  unpack_key_base64(client_data[2].encode('utf-8')),
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
                    client_id_hex = pack_key_hex(client['client_id'].encode('utf-8'))
                    client_name = client['name']
                    password_hash_base64 = pack_key_base64(client['password_hash'])
                    last_seen = client['last_seen']

                    file.write(f"{client_id_hex}:{client_name}:{password_hash_base64}:{last_seen}\n")
        except IOError:
            print(f"Error: Unable to save clients to file '{self.file_path}'")
        except Exception as e:
            print(f"Error: ", e)

    def is_exist(self, other_client):
        is_exist = False
        for client in self.clients:
            if client["name"] == other_client["name"]:
                is_exist = True
                break
                
        return is_exist

    def get_password_hash_by_client_id(self, client_id):
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

