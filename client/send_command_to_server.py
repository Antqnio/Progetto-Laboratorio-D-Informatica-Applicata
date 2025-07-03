# client/send_command_to_server.py
"""
This module contains the function to send commands to the server over TCP.
It uses a multiprocessing queue to receive commands from
the get_result function (a function in gesture_recognizer.py).
"""

import multiprocessing
import socket
import sys
import signal
import ctypes

# TCP server configuration
SERVER_IP = "host.docker.internal"
SERVER_PORT = 9000



# TCP communication with the command server
def send_command_to_server(gesture_recognizer_to_socket_queue : "multiprocessing.Queue", server_is_running : "ctypes.c_bool") -> None:
    """
    Continuously retrieves commands from a multiprocessing queue and sends them to a server over a TCP socket.

    Args:
        gesture_recognizer_to_socket_queue (multiprocessing.Queue): A queue from which commands are received to be sent to the server.
        server_is_running (ctypes.c_bool): A shared boolean value indicating whether the server is running. This function will set this value to True when the connection is established and to False if the connection is lost.
    Returns:
        None
    Behavior:
        - Connects to the server using SERVER_IP and SERVER_PORT.
        - Waits for commands from the queue, appends a delimiter '|', and sends them to the server.
        - If no command is received (i.e., command is None), prints an info message and breaks the loop.
        - Handles connection errors and prints error messages if the connection fails.
        - If the connection is lost, it will attempt to reconnect indefinitely.
    """
    
    
    def handle_sigterm(signum, frame) -> None:
        """
        Handle the SIGTERM signal by printing an informational message and exiting the program.

        Args:
            signum (int): The signal number received (typically signal.SIGTERM).
            frame (FrameType): The current stack frame (unused).

        Returns:
            None
        """
        print("[INFO] received SIGTERM. Closing connection and exiting...")
        sys.exit(0)
    
    
    # Print server connection details
    print(f"[INFO] Server IP: {SERVER_IP}, Port: {SERVER_PORT}")
    # Create a signal handler for SIGTERM to gracefully close the connection
    signal.signal(signal.SIGTERM, handle_sigterm)
    s = None # Initialize socket to None to avoid UnboundLocalError in case of exception before connection
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_IP, SERVER_PORT))
                print("[INFO] Connected to server successfully.")
                # Set the server_is_running flag to True to signal that the server is running to flask_client.py
                server_is_running.value = True
                while True:
                    # Wait for a command from the queue
                    command = gesture_recognizer_to_socket_queue.get()
                    if command is None:
                        print("[INFO] Popped argument is None: received, exiting...")
                        return
                    print(f"[INFO] Sending command to server: {command}")
                    s.sendall(command.encode())
        except SystemExit:
            # Handle SystemExit to gracefully exit the process
            if s is not None:
                try:
                    s.shutdown(socket.SHUT_RDWR) # Not needed, but can be used to close the socket gracefully
                except Exception:
                    pass
            raise # Pass the SystemExit exception to exit the process
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"[ERROR] Lost connection to server: {e}")
            server_is_running.value = False
        except Exception as e:
            print(f"[ERROR] Connection to server failed: {e}")