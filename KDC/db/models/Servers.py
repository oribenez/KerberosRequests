import os
import threading

from KDC.db.models.RecordAlreadyExist import RecordAlreadyExist
from lib.utils import pack_key_hex, pack_key_base64, unpack_key_hex, unpack_key_base64


class Servers:

    def __init__(self, file_path='/db/data/servers'):
        self.servers = []
        self.lock = threading.Lock()
        self.file_path = file_path

        self.load_servers_from_file()

    def load_servers_from_file(self):
        with self.lock:
            servers_temp = []

            try:
                with open(os.getcwd()+self.file_path, 'r') as file:
                    for line in file:
                        server_data = line.strip().split(':')
                        if len(server_data) == 3:
                            server = {
                                'server_id': unpack_key_hex(server_data[0].encode('utf-8')).decode('utf-8'),
                                'name': server_data[1],
                                'aes_key': unpack_key_base64(server_data[2].encode('utf-8')),
                            }
                            servers_temp.append(server)

                    self.servers = list(servers_temp)  # shallow copy
            except (FileNotFoundError, IOError):
                print(f"Error: Unable to load servers from file '{self.file_path}'")

    def save_servers_to_file(self):
        with self.lock:
            try:
                with open(os.getcwd()+self.file_path, 'w') as file:
                    for server in self.servers:
                        server_id_hex = pack_key_hex(server['server_id'].encode('utf-8'))
                        server_name = server['name']
                        server_aes_key_base64 = pack_key_base64(server['aes_key'])

                        file.write(f"{server_id_hex}:{server_name}:{server_aes_key_base64}\n")

            except IOError:
                print(f"Error: Unable to save servers to file '{self.file_path}'")
            except Exception as e:
                print(f"Error: ", e)

    def is_exist(self, other_server):
        is_exist = False
        for server in self.servers:
            if server["name"] == other_server["name"]:
                is_exist = True
                break

        return is_exist

    def get_all_servers(self):
        servers_list = []
        for server in self.servers:
            servers_list += [{
                "server_id": server["server_id"],
                "name": server["name"]
            }]

        return servers_list

    def get_aes_key_by_server_id(self, server_id):
        for server in self.servers:
            if server["server_id"] == server_id:
                return server["aes_key"]

    def add_server(self, server):
        # check if client already exist by name
        if self.is_exist(server):
            err_msg = "Server already exist"
            print(err_msg)
            raise RecordAlreadyExist(err_msg)
        else:
            self.servers.append(server)
            self.save_servers_to_file()
