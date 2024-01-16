import threading


class Servers:

    def __init__(self, file_path='../data/servers'):
        self.servers = []
        self.lock = threading.Lock()
        self.file_path = file_path

        self.load_servers_from_file()

    def load_servers_from_file(self):
        with self.lock:
            servers_temp = []

            try:
                with open(self.file_path, 'r') as file:
                    for line in file:
                        server_data = line.strip().split(':')
                        if len(server_data) == 4:
                            server = {
                                'ID': server_data[0],
                                'Name': server_data[1],
                                'AESKey': server_data[2],
                            }
                            servers_temp.append(server)

                    self.servers = list(servers_temp)  # shallow copy
            except (FileNotFoundError, IOError):
                print(f"Error: Unable to load servers from file '{self.file_path}'")

    def save_servers_to_file(self):
        with self.lock:
            try:
                with open(self.file_path, 'w') as file:
                    for server in self.servers:
                        file.write(f"{server['ID']}:{server['Name']}:{server['AESKey']}\n")
            except IOError:
                print(f"Error: Unable to save servers to file '{self.file_path}'")

    def add_server(self, server):
        with self.lock:
            # TODO: check if server already exist
            self.servers.append(server)
            self.save_servers_to_file()
