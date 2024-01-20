import os
import threading

from KDC.db.models.RecordAlreadyExist import RecordAlreadyExist


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
                                'server_id': server_data[0],
                                'name': server_data[1],
                                'aes_key': server_data[2],
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
                        file.write(f"{server['server_id']}:{server['name']}:{server['aes_key']}\n")
            except IOError:
                print(f"Error: Unable to save servers to file '{self.file_path}'")

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
