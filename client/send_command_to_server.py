# client/send_command_to_server.py
"""
This module contains the function to send commands to the server over TCP.
It uses a multiprocessing queue to receive commands from
the get_result function (a function in gesture_recognizer.py).
"""

import multiprocessing
import socket

# TCP server configuration
SERVER_IP = "host.docker.internal"
SERVER_PORT = 9000



# TCP communication with the command server
def send_command_to_server(client_to_server_queue : "multiprocessing.Queue"):
    """
    Continuously retrieves commands from a multiprocessing queue and sends them to a server over a TCP socket.

    Args:
        client_to_server_queue (multiprocessing.Queue): A queue from which commands are received to be sent to the server.

    Behavior:
        - Connects to the server using SERVER_IP and SERVER_PORT.
        - Waits for commands from the queue, appends a delimiter '|', and sends them to the server.
        - If no command is received (i.e., command is None), prints an info message and breaks the loop.
        - Handles connection errors and prints error messages if the connection fails.
        - If the connection is lost, it will attempt to reconnect indefinitely.
    """
    # Print server connection details
    print(f"[INFO] Server IP: {SERVER_IP}, Port: {SERVER_PORT}")
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_IP, SERVER_PORT))
                while True:
                    # Wait for a command from the queue
                    command = client_to_server_queue.get()
                    command = command + "|"
                    if command is None:
                        print("[INFO] No command received, exiting...")
                        break
                    print(f"[INFO] Sending command to server: {command}")
                    s.sendall(command.encode())
        except Exception as e:
            print(f"[ERROR] Connection to server failed: {e}")