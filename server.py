import socket
import threading

HOST = '0.0.0.0'  # listen on all network interfaces
PORT = 9000       # port exposed by the container

def handle_client(conn, addr):
    print(f"[INFO] Connection from {addr}")
    with conn:
        while True:
            data = conn.recv(1024)       # read up to 1024 bytes
            if not data:
                # client has closed the connection
                print(f"[INFO] Connection closed by {addr}")
                break

            # decode bytes into a UTF-8 string
            try:
                message = data.decode('utf-8')
            except UnicodeDecodeError:
                print(f"[ERROR] Failed to decode data from {addr}")
                continue

            # process the received string
            print(f"[RECEIVED] {message}")

            # (optional) send an acknowledgment back to the client
            response = f"ACK: received '{message}'"
            conn.sendall(response.encode('utf-8'))
    # end handle_client

def main():
    # create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # allow reuse of the address (avoid “Address already in use” errors)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((HOST, PORT))
        s.listen()
        print(f"[START] Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            # handle each client connection in a separate daemon thread
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()

if __name__ == '__main__':
    main()
