import os
import json
from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
import cv2
import multiprocessing
from src.gesture_recognizer.gesture_recognizer import start_gesture_recognition
from client.client_constants import COMMANDS
import re

# Flask app setup
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)


# List of available gestures and commands
GESTURES = ["Thumb_Up", "Thumb_Down", "Open_Palm", "Closed_Fist", "Victory", "ILoveYou", "Pointing_Up"]

# Gesture-command mapping
gesture_to_command = {}

# Queue for inter-process communication between client and Windows server.
client_to_server_queue = None

# Recognition state
recognition_active = False

# Directory to store configuration files
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "static/configs")
os.makedirs(CONFIG_DIR, exist_ok=True)


def is_valid_config_name(name : str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]+$', name))



# Home route (index.html)
@app.route("/", methods=["GET", "POST"])
def index():
    global gesture_to_command

    # List of available configuration files (without .json extension)
    config_files = [f[:-5] for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    selected_config = request.form.get("config_name_select") or request.form.get("config_name_text", "")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "apply":
            # Aggiorna gesture_to_command ma NON salva su file
            for gesture in GESTURES:
                command = request.form.get(gesture)
                if command:
                    gesture_to_command[gesture] = command
                elif gesture in gesture_to_command:
                    del gesture_to_command[gesture]
            return jsonify({"status": "ok", "message": "Configuration applied successfully."})
        elif action == "save" and is_valid_config_name(selected_config):
            # Aggiorna gesture_to_command e salva su file
            for gesture in GESTURES:
                print(f"[INFO] Processing gesture: {gesture}")
                command = request.form.get(gesture)
                print(f"[INFO] Associated command: {command}")
                gesture_to_command[gesture] = command
                #if command:
                #    gesture_to_command[gesture] = command
                #elif gesture in gesture_to_command:
                #    del gesture_to_command[gesture]
            if selected_config:
                path = os.path.join(CONFIG_DIR, selected_config + ".json")
                with open(path, "w") as f:
                    json.dump(gesture_to_command, f, indent=2)
                return jsonify({"status": "ok", "message": "Configuration saved successfully."})
            else:
                return jsonify({"status": "error", "message": "No selected configuration."}, 400)
        else:
            print(f"[ERROR] Unknown action: {action}")
            return jsonify({"status": "error", "message": "Unknown action."}, 400)
    # GET (usata quando l'utente chiede di vedere i file .json salvati in precedenza) o prima apertura
    return render_template(
        "index.html",
        gestures=GESTURES,
        commands=COMMANDS,
        mappings=gesture_to_command,
        active=recognition_active,
        configs=config_files,
        selected_config=selected_config
    )


recognition_process = None
webcam_frame_queue = None

@app.route("/start")
def start_recognition():
    
    
    global recognition_active, recognition_process

    if not recognition_active:
        recognition_active = True
        # Initialize queue for inter-process communication
        global webcam_frame_queue
        webcam_frame_queue = multiprocessing.Queue()
        # Pass gesture_to_command as an argument
        global gesture_to_command
        global client_to_server_queue
        recognition_process = multiprocessing.Process(
            target=start_gesture_recognition,
            args=(gesture_to_command, webcam_frame_queue, client_to_server_queue),
        )
        recognition_process.start()
        print("[INFO] Gesture recognition process started.")
    return jsonify({"status": "ok", "active": True})

@app.route("/stop")
def stop_recognition():
    global recognition_active, recognition_process
    if recognition_active is False:
        return jsonify({"status": "no", "active": False})
    recognition_active = False
    if recognition_process and recognition_process.is_alive():
        recognition_process.terminate()
        #recognition_process.join()
        print("Stopping recognition...")
        global webcam_frame_queue
        webcam_frame_queue.close()
        webcam_frame_queue.join_thread()
        recognition_process = None
        print("[INFO] Gesture recognition process stopped.")

    return jsonify({"status": "ok", "active": False})

@app.route("/video_feed")
def video_feed():
    def generate():
        print("[INFO] Starting video feed...")
        while recognition_active:
            frame = webcam_frame_queue.get() if webcam_frame_queue else None
            if frame is None:
                continue
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


