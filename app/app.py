import os
import json
from flask import Flask, render_template, request, redirect, url_for
import socket
import threading
import subprocess
from threading import Event




# Dynamically get the Windows host IP address
# This function assumes that the server is running on a Windows machine
# and retrieves the IP address of the nameserver from the resolv.conf file.
# If it fails, it returns a fallback IP.
def get_windows_host_ip():
    try:
        output = subprocess.check_output("cat /etc/resolv.conf | grep nameserver", shell=True)
        return output.decode().split()[1]
    except Exception:
        return "127.0.0.1"  # fallback

# Flask app setup
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '..', 'static')
)

# TCP server configuration
SERVER_IP = "host.docker.internal"
SERVER_PORT = 9000

# List of available gestures and commands
GESTURES = ["Thumb_Up", "Thumb_Down", "Open_Palm", "Closed_Fist", "Victory", "ILoveYou", "Pointing_Up"]
COMMANDS = ["Volume_Up", "Volume_Down", "Open_Calculator", "Open_Chrome", "Take_Screenshot"]

# Gesture-command mapping
gesture_to_command = {}

# Recognition state
recognition_active = False

# Directory to store configuration files
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Send recognized result to the TCP server
def send_result(result: str, gesture_to_command: dict):
    print(f"[INFO] Recognized gesture: {result}")
    command = gesture_to_command.get(result)
    if command in COMMANDS:
        print(f"[INFO] Sending associated command: {command}")
        send_command_to_server(command)

# TCP communication with the command server
def send_command_to_server(command: str):
    print(f"[INFO] Server IP: {SERVER_IP}, Port: {SERVER_PORT}")
    print(f"[INFO] Sending command to server: {command}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            s.sendall(command.encode())
    except Exception as e:
        print(f"[ERROR] Connection to server failed: {e}")

# Home route (index.html)
@app.route("/", methods=["GET", "POST"])
def index():
    global gesture_to_command

    # List of available configuration files (without .json extension)
    config_files = [f[:-5] for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    selected_config = request.form.get("config_name", "")

    if request.method == "POST":
        action = request.form.get("action")

        # Apply changes from the form
        if action == "Applica":
            for gesture in GESTURES:
                command = request.form.get(gesture)
                if command:
                    gesture_to_command[gesture] = command
                elif gesture in gesture_to_command:
                    del gesture_to_command[gesture]

        # Save configuration to file
        elif action == "Salva":
            if selected_config:
                path = os.path.join(CONFIG_DIR, selected_config + ".json")
                with open(path, "w") as f:
                    json.dump(gesture_to_command, f, indent=2)

        # Load configuration from file
        elif action == "Carica":
            if selected_config:
                path = os.path.join(CONFIG_DIR, selected_config + ".json")
                if os.path.exists(path):
                    with open(path, "r") as f:
                        gesture_to_command = json.load(f)

        return redirect(url_for("index"))

    return render_template(
        "index.html",
        gestures=GESTURES,
        commands=COMMANDS,
        mappings=gesture_to_command,
        active=recognition_active,
        configs=config_files,
        selected_config=selected_config
    )

# Start gesture recognition
stop_event = Event()

@app.route("/start")
def start_recognition():
    from src.gesture_recognizer.gesture_recognizer import start_gesture_recognition
    global recognition_active, stop_event
    if not recognition_active:
        recognition_active = True
        stop_event.clear()
        threading.Thread(target=start_gesture_recognition, args=(gesture_to_command, stop_event,), daemon=True).start()
    return redirect(url_for("index"))

# Stop gesture recognition
@app.route("/stop")
def stop_recognition():
    global recognition_active
    recognition_active = False
    stop_event.set()
    return redirect(url_for("index"))

# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
