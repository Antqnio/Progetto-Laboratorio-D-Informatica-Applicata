import socket
import threading
import signal
import sys

HOST = '0.0.0.0'
PORT = 9000


def handle_client(conn, addr):
    print(f"[INFO] Connection from {addr}")
    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    print(f"[INFO] Connection closed by {addr}")
                    break
                message = data.decode('utf-8')
                print(f"[RECEIVED] {message}")
                response = f"ACK: received '{message}'"
                conn.sendall(response.encode('utf-8'))
            except ConnectionResetError:
                print(f"[WARN] Connection reset by {addr}")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                break

def main():
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)  # timeout di 1 secondo per uscire dal blocco accept()

        print(f"[START] Server listening on {HOST}:{PORT}")

        while True:
            try:
                conn, addr = s.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ERROR] {e}")
                break

        print("[STOP] Server arrestato")

if __name__ == '__main__':
    main()
