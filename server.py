import socket
import threading
import pythoncom

import ctypes

def simulate_volume_key(key, steps=3):
    # key: 'up' o 'down'
    VK_VOLUME_UP = 0xAF
    VK_VOLUME_DOWN = 0xAE
    if key == 'up':
        vk = VK_VOLUME_UP
    elif key == 'down':
        vk = VK_VOLUME_DOWN
    else:
        return
    for _ in range(steps):
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)

def volume_up():
    simulate_volume_key('up') # aumenta di 10%

def volume_down():
    simulate_volume_key('down') # diminuisce di 10%

HOST = '0.0.0.0'  # listen on all network interfaces
PORT = 9000       # port exposed by the container

def handle_client(conn, addr):
    pythoncom.CoInitialize()  # Initialize COM for the current thread
    print(f"[INFO] Connection from {addr}")
    try:
        with conn:
            while True:
                data = conn.recv(1024)       # read up to 1024 bytes
                """
                if not data:
                    # client has closed the connection
                    print(f"[INFO] Connection closed by {addr}")
                    break
                """
                # decode bytes into a UTF-8 string
                try:
                    message = data.decode('utf-8')
                except UnicodeDecodeError:
                    print(f"[ERROR] Failed to decode data from {addr}")
                    continue

                # process the received string
                if message is not None and message not in ["", " "]:
                    # Log the received message
                    print(f"[RECEIVED] {message}")
                
                # Esegui azioni in base al messaggio ricevuto
                if message == "Volume_Up":
                    volume_up()
                    response = "Volume increased"
                elif message == "Volume_Down":
                    volume_down()
                    response = "Volume decreased"
                # else:
    finally:
        pythoncom.CoUninitialize()  # De-initialize COM per evitare errori di access violation
    # end handle_client

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
                print(f"[INFO] Accepted connection from {addr}")
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
