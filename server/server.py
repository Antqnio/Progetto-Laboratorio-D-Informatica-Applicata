import socket
import threading
import pythoncom
import ctypes
import time

def simulate_volume_key(key, steps=1):
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
    simulate_volume_key('up')

def volume_down():
    simulate_volume_key('down')

def simulate_alt_tab():
    VK_MENU = 0x12  # Alt
    VK_TAB = 0x09   # Tab
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 0, 0)  # Alt down
    ctypes.windll.user32.keybd_event(VK_TAB, 0, 0, 0)   # Tab down
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_TAB, 0, 2, 0)   # Tab up
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 2, 0)  # Alt up

def simulate_media_play_pause():
    VK_MEDIA_PLAY_PAUSE = 0xB3
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)

HOST = '0.0.0.0'
PORT = 9000

def handle_client(conn, addr):
    pythoncom.CoInitialize()
    print(f"[INFO] Connection from {addr}")
    try:
        with conn:
            while True:
                data = conn.recv(1024)
                try:
                    message = data.decode('utf-8')
                except UnicodeDecodeError:
                    print(f"[ERROR] Failed to decode data from {addr}")
                    continue

                if message is not None and message.strip() != "":
                    print(f"[RECEIVED] {message}")

                if message == "Volume Up":
                    volume_up()
                    response = "Volume increased"
                elif message == "Volume Down":
                    volume_down()
                    response = "Volume decreased"
                elif message == "AltTab":
                    simulate_alt_tab()
                    response = "Alt+Tab sent"
                elif message == "PlayPause":
                    simulate_media_play_pause()
                    response = "Media play/pause triggered"
                else:
                    response = f"Unknown command: {message}"

                try:
                    conn.sendall(response.encode('utf-8'))
                except:
                    pass
    finally:
        pythoncom.CoUninitialize()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)
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
