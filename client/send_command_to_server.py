import multiprocessing
import socket

# TCP server configuration
SERVER_IP = "host.docker.internal"
SERVER_PORT = 9000



# TCP communication with the command server
def send_command_to_server(client_to_server_queue : "multiprocessing.Queue"):
    print(f"[INFO] Server IP: {SERVER_IP}, Port: {SERVER_PORT}")
    try:
        while True:
            # Wait for a command from the queue
            command = client_to_server_queue.get()
            if command is None:
                print("[INFO] No command received, exiting...")
                break
            print(f"[INFO] Sending command to server: {command}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_IP, SERVER_PORT))
                s.sendall(command.encode())
    except Exception as e:
        print(f"[ERROR] Connection to server failed: {e}")