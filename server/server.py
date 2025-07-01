import socket
import threading
import pythoncom
import ctypes
import time
import psutil
import subprocess
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

# Server configuration
HOST = '0.0.0.0'
PORT = 9000

# Constants for mouse events
MOUSEEVENTF_WHEEL = 0x0800


def calculator_already_running() -> bool: 
    """Check if the calculator is already running."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() in ["calculator.exe", "calc.exe", "calculatorapp.exe", "applicationframehost.exe"]:
            return True
    return False

def task_manager_already_running() -> bool:
    """Check if the Task Manager is already running."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == "taskmgr.exe":
            return True
    return False

# Volume Functions
def get_master_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current_volume = volume.GetMasterVolumeLevelScalar()
    return int(current_volume * 100)

def simulate_volume_key(key, steps=3):
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
    if get_master_volume() < 100:
        simulate_volume_key('up')
        return "Volume increased"
    return "Volume already at 100%"

def volume_down():
    if get_master_volume() > 0:
        simulate_volume_key('down')
        return "Volume decreased"
    return "Volume already at 0%"

# Altri comandi
def simulate_alt_tab():
    VK_MENU = 0x12
    VK_TAB = 0x09
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_TAB, 0, 0, 0)
    time.sleep(2.5)
    ctypes.windll.user32.keybd_event(VK_TAB, 0, 2, 0)
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 2, 0)

def simulate_media_play_pause():
    VK_MEDIA_PLAY_PAUSE = 0xB3
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)

def open_calculator():
    # Avvia calc.exe
    subprocess.Popen("calc.exe")
    time.sleep(3)

def simulate_print_screen():
    VK_SNAPSHOT = 0x2C
    ctypes.windll.user32.keybd_event(VK_SNAPSHOT, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_SNAPSHOT, 0, 2, 0)

def scroll_mouse(amount):
    # amount: positivo = su, negativo = giù
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, amount, 0)

def open_task_manager():
    subprocess.Popen("taskmgr.exe", shell=True)

# TCP Server
def handle_client(conn, addr):
    pythoncom.CoInitialize()
    print(f"[INFO] Connection from {addr}")
    try:
        with conn:
            last_command = ""
            while True:
                data = conn.recv(1024)
                try:
                    # split by '|' into an array and take the first element
                    command = data.decode('utf-8').strip().split('|')[0] 
                except UnicodeDecodeError:
                    print(f"[ERROR] Failed to decode data from {addr}")
                    continue

                if not command:
                    continue
                print(f"[INFO] Last Command: {last_command}")
                print(f"[RECEIVED] {command}")

                if command == "Volume Up":
                    response = volume_up()
                elif command == "Volume Down":
                    response = volume_down()
                elif command == "AltTab":
                    simulate_alt_tab()
                    response = "Alt+Tab sent"
                elif command == "PlayPause":
                    simulate_media_play_pause()
                    response = "Media play/pause triggered"
                elif command == "Open Calculator":
                    if last_command == "Open Calculator" and calculator_already_running():
                        print("[INFO] Calculator already running, skipping command")
                        continue
                    open_calculator()
                    response = "Calculator opened"
                elif command == "Screenshot":
                    simulate_print_screen()
                    response = "Screenshot key (Print Screen) sent"
                elif command == "Scroll Up":
                    scroll_mouse(120)
                    response = "Mouse scrolled up"
                elif command == "Scroll Down":
                    scroll_mouse(-120)
                    response = "Mouse scrolled down"
                elif command == "Task Manager":
                    if last_command == "Task Manager" and task_manager_already_running():
                        print("[INFO] Task Manager already running, skipping command")
                        continue
                    open_task_manager()
                    response = "Task Manager opened"
                else:
                    response = f"Unknown command: {command}"
                last_command = command
                print(f"[RESPONSE] {response}")
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
