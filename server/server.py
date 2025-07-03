# server.py
# -*- coding: utf-8 -*-
"""This module implements a TCP server that listens for commands from a client and executes system-level actions based on those commands.
It supports commands such as volume control, opening applications, simulating key presses, and mouse actions.
The server uses Python's socket library for networking, threading for handling multiple clients, and pycaw for audio control on Windows.
It also uses psutil to check if certain applications are already running before executing commands to avoid duplicates.
The server runs indefinitely, accepting connections and processing commands until it is manually stopped.
"""

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
    """
    Checks if a calculator application is currently running on the system.
    Iterates through all running processes and checks if any process name matches
    common calculator application executables (e.g., "calculator.exe", "calc.exe", 
    "calculatorapp.exe", "applicationframehost.exe").
    Args:
        None
    Returns:
        bool: True if a calculator application is running, False otherwise.
    """
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() in ["calculator.exe", "calc.exe", "calculatorapp.exe", "applicationframehost.exe"]:
            return True
    return False

def task_manager_already_running() -> bool:
    """
    Checks if the Windows Task Manager process ("taskmgr.exe") is currently running.
    Args:
        Noner
    Returns:
        bool: True if Task Manager is running, False otherwise.
    """
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == "taskmgr.exe":
            return True
    return False

# Volume Functions
def get_master_volume() -> int:
    """
    Retrieves the current master volume level of the system as a percentage.
    Args:
        None
    Returns:
        int: The current master volume level, scaled from 0 to 100.
    """
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current_volume = volume.GetMasterVolumeLevelScalar()
    return int(current_volume * 100)

def simulate_volume_key(key : str, steps : int = 3) -> None:
    """
    Simulates pressing the system volume up or down key a specified number of times.
    Args:
        key (str): The volume key to simulate. Accepts 'up' for volume up or 'down' for volume down.
        steps (int, optional): The number of times to simulate the key press. Defaults to 3.
    Returns:
        None
    Note:
        This function uses Windows-specific APIs via ctypes and will only work on Windows platforms.
    """
    
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

def volume_up() -> str:
    """
    Increases the system's master volume by one step if it is below 100%.
    Args:
        None
    Returns:
        str: A message indicating whether the volume was increased or already at maximum.
    """
    
    if get_master_volume() < 100:
        simulate_volume_key('up')
        return "Volume increased"
    return "Volume already at 100%"

def volume_down() -> str:
    """
    Decreases the system's master volume by one step if it is above 0%.
    Args:
        None
    Returns:
        str: A message indicating whether the volume was decreased or already at 0%.
    """
    
    if get_master_volume() > 0:
        simulate_volume_key('down')
        return "Volume decreased"
    return "Volume already at 0%"

# Other commands
def simulate_alt_tab() -> None:
    """
    Simulates the "Alt+Tab" keyboard shortcut on Windows to switch between open applications.
    This function programmatically presses and holds the Alt key, then presses the Tab key to open the window switcher.
    It waits for a short period (2.5 seconds) to allow the user to select a window, then releases both keys.
    Useful for automating window switching in GUI automation tasks.
    Args:
        None
    Returns:
        None
    Note:
        This function is intended for use on Windows systems and requires the `ctypes` and `time` modules.
    """
    
    VK_MENU = 0x12
    VK_TAB = 0x09
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_TAB, 0, 0, 0)
    # Give some time to the user to select a window
    # before releasing the keys, otherwise it will switch immediately
    # to the next window without giving the user a chance to select one.
    time.sleep(2.5)
    ctypes.windll.user32.keybd_event(VK_TAB, 0, 2, 0)
    ctypes.windll.user32.keybd_event(VK_MENU, 0, 2, 0)

def simulate_media_play_pause() -> None:
    """
    Simulates pressing the media play/pause key on a Windows system.
    This function uses the Windows API to send a key event corresponding to the
    media play/pause button (VK_MEDIA_PLAY_PAUSE). It can be used to control media
    playback in compatible applications.
    Args:
        None
    Returns:
        None
    Note:
        This function is specific to Windows platforms and requires the `ctypes` module.
    Raises:
        AttributeError: If called on a non-Windows platform where `ctypes.windll.user32` is unavailable.
    """
    
    VK_MEDIA_PLAY_PAUSE = 0xB3
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)

def open_calculator() -> None:
    """
    Opens the Windows Calculator application and waits for 3 seconds.
    This function launches 'calc.exe' using a subprocess and then pauses execution for 3 seconds.
    To give time for the application to open before proceeding with any further actions.
    """
    
    subprocess.Popen("calc.exe")
    time.sleep(3)

def simulate_print_screen() -> None:
    """
    Simulates pressing the Print Screen key on a Windows system.
    This function uses the Windows API to programmatically trigger the Print Screen
    key event, which captures the current screen to the clipboard.
    """

    VK_SNAPSHOT = 0x2C
    ctypes.windll.user32.keybd_event(VK_SNAPSHOT, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_SNAPSHOT, 0, 2, 0)

def scroll_mouse(amount : int) -> None:
    """
    Scrolls the mouse wheel by a specified amount.

    Args:
        amount (int): The amount to scroll the mouse wheel. Positive values scroll up, negative values scroll down.

    Returns:
        None
    """
    # amount: positive = up, negative = down
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, amount, 0)

def open_task_manager() -> None:
    """
    Opens the Windows Task Manager by launching 'taskmgr.exe' as a separate process.
    This function uses subprocess.Popen to start the Task Manager application.
    Note: This function is intended for use on Windows operating systems.
    Args:
        None
    Returns:
        None
    """
    
    subprocess.Popen("taskmgr.exe", shell=True)

# TCP Server
def handle_client(conn, addr) -> None:
    """
    Handles a client connection, processes incoming commands, and sends appropriate responses.

    This function listens for commands sent by the client over the given connection,
    executes corresponding system actions (such as adjusting volume, simulating key presses,
    opening applications, etc.), and sends a response back to the client. It maintains the
    state of the last command to avoid redundant actions (e.g., not opening Calculator or
    Task Manager if already running). The function also handles decoding errors and ensures
    COM initialization and cleanup for thread safety.

    Args:
        conn: The socket connection object to communicate with the client.
        addr: The address of the connected client.

    Returns:
        None
    """
    pythoncom.CoInitialize()
    print(f"[INFO] Connection from {addr}")
    try:
        with conn:
            while True:
                # Set a timeout for receiving data to avoid blocking indefinitely
                data = conn.recv(1024)
                try:
                    # Split by '|' into an array and take the first element.
                    # To avoid issues where tcp buffers commands and sends them in chunks
                    command = data.decode('utf-8').strip().split('|')[0] 
                except UnicodeDecodeError:
                    print(f"[ERROR] Failed to decode data from {addr}")
                    continue
                # If command is empty, skip processing to speed up the loop
                if not command:
                    continue
                    
                print(f"[RECEIVED] {command}")
                
                # Process the command
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
                    if calculator_already_running():
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
                    if task_manager_already_running():
                        print("[INFO] Task Manager already running, skipping command")
                        continue
                    open_task_manager()
                    response = "Task Manager opened"
                else:
                    response = f"Unknown command: {command}"
                
                print(f"[RESPONSE] {response}")
    finally:
        # Deinitialize COM to clean up resources
        pythoncom.CoUninitialize()
        

def main():
    """
    Starts a TCP server that listens for incoming client connections on the specified HOST and PORT.
    For each accepted connection, a new daemon thread is spawned to handle the client using the handle_client function.
    The server socket is configured to allow address reuse and has a timeout for accepting connections.
    Logs server start, accepted connections, errors, and server shutdown events.
    Args:
        None
    Returns:
        None
    """
    # Initialize the server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Set socket options to allow address reuse
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the specified host and port
        s.bind((HOST, PORT))
        # Start listening for incoming connections
        s.listen()
        # Set a timeout for accepting connections to avoid blocking indefinitely and accept Ctrl+C
        s.settimeout(1.0)
        print(f"[START] Server listening on {HOST}:{PORT}")
        while True:
            try:
                # Accept a new client connection
                conn, addr = s.accept()
                print(f"[INFO] Accepted connection from {addr}")
                # Create a new thread to handle the client connection
                # Use daemon threads so they will exit when the main thread exits
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except socket.timeout:
                # If no connection is accepted within the timeout, continue to check for new connections
                continue
            except Exception as e:
                # Catch any other exceptions (like KeyboardInterrupt, launched with CTRL+C) and print an error message
                print(f"[ERROR] {e}")
                break
        print("[STOP] Server arrested")

if __name__ == '__main__':
    main()
