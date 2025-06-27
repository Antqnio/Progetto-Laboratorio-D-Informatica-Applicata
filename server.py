import socket
import threading
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import signal
import sys

def set_volume(change):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current = volume.GetMasterVolumeLevelScalar()
    new_volume = min(max(current + change, 0.0), 1.0)
    volume.SetMasterVolumeLevelScalar(new_volume, None)
    return new_volume

def volume_up():
    return set_volume(0.1)  # aumenta di 10%

def volume_down():
    return set_volume(-0.1) # diminuisce di 10%

HOST = '172.20.112.1'  # listen on all network interfaces
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
            
            # Esegui azioni in base al messaggio ricevuto
            if message.lower() == "Volume_Up":
                vol = volume_up()
                response = f"Volume increased to {int(vol*100)}%"
            elif message.lower() == "volume down":
                vol = volume_down()
                response = f"Volume decreased to {int(vol*100)}%"
            # else:

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
