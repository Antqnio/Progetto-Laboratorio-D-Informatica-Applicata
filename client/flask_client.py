# client/flask_client.py
# -*- coding: utf-8 -*-
"""
This module contains the Flask web application for the gesture recognition client.
It provides routes for displaying the main configuration page, starting and stopping gesture recognition,
and streaming video from the webcam.
The application allows users to map gestures to commands, save configurations, and view the video feed
from the webcam in real-time.
"""
import os
import signal
import json
from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
import cv2
import multiprocessing
import ctypes
import re
from src.gesture_recognizer.gesture_recognizer import start_gesture_recognition
from client_constants import COMMANDS, GESTURES
from queue import Empty

# Flask app setup
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)



# Gesture-command mapping
gesture_to_command = {}

# Queue for inter-process communication between client and Windows server.
gesture_recognizer_to_socket_queue = None
# Boolean value to indicate if the server is running. This will be updated by the send_command_to_server function.
server_is_running = multiprocessing.Value(ctypes.c_bool, True)

# multiprocessing.Array for inter-process communication between gesture_recognizer.py and flask_client.py
# gesture_recognizer.py will write the last recognized gesture in last_gesture multiprocessing.Array and
# flask_client.py will send it to the web interface.
last_gesture = None


# Directory to store configuration files
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "static/configs")
os.makedirs(CONFIG_DIR, exist_ok=True)


def is_valid_config_name(name : str) -> bool:
    """
    Checks if the provided configuration name is valid.
    A valid configuration name must:
    - Be a non-empty string.
    - Contain only alphanumeric characters and underscores.
    Args:
        name (str): The configuration name to validate.
    Returns:
        bool: True if the name is valid, False otherwise.
    """
    
    return len(name) > 0 and bool(re.match(r'^[a-zA-Z0-9_]+$', name))



# Home route (index.html)
@app.route("/", methods=["GET", "POST"])
def index():
    """
    Flask route for the index page ("/") that handles both GET and POST requests.

    GET:
        - Renders the main configuration page, displaying available gesture-command mappings,
        available commands, and saved configuration files.

    POST:
        - Handles two main actions from the form:
            1. "apply": Updates the in-memory gesture-to-command mapping (`gesture_to_command`)
            based on the submitted form data, but does not save changes to disk.
            Returns a JSON response indicating success.
            2. "save": Updates the in-memory mapping and saves the configuration to a JSON file
            if a valid configuration name is provided. Returns a JSON response indicating
            success or error if no configuration name is selected.
        - If an unknown action is received, returns a JSON error response.

    Args:
        None (uses Flask's `request` object for form data).

    Returns:
        - For GET requests: Renders the "index.html" template with gesture, command, and configuration data.
        - For POST requests: Returns a JSON response indicating the result of the action.
    """
    global gesture_to_command

    # List of available configuration files (without .json extension)
    config_files = [f[:-5] for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
    
    # Used only for the "save" action
    # request.form.get("config_name_select") is used when the user selects a config from the dropdown
    # request.form.get("config_name_text") is used when the user types a new config
    # If both are empty, selected_config will be an empty string
    selected_config = request.form.get("config_name_select") or request.form.get("config_name_text", "")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "apply":
            # Update gesture_to_command but does not save to file
            for gesture in GESTURES:
                # We receive the gesture name as a string from the form, which is a FormData JavaScript object
                command = request.form.get(gesture)
                if command:
                    gesture_to_command[gesture] = command
                elif gesture in gesture_to_command:
                    del gesture_to_command[gesture]
            return jsonify({"status": "ok", "message": "Configuration applied successfully."})
        elif action == "save" and is_valid_config_name(selected_config):
            print("[INFO] Valid configuration name")
            # Update gesture_to_command and saves configuration in a file
            for gesture in GESTURES:
                print(f"[INFO] Processing gesture: {gesture}")
                command = request.form.get(gesture)
                print(f"[INFO] Associated command: {command}")
                gesture_to_command[gesture] = command
            if selected_config:
                # Save the current gesture_to_command mapping to a JSON file
                path = os.path.join(CONFIG_DIR, selected_config + ".json")
                with open(path, "w") as f:
                    json.dump(gesture_to_command, f, indent=2)
                return jsonify({"status": "ok", "message": "Configuration saved and applied successfully."})
            else:
                return jsonify({"status": "error", "message": "No selected configuration."}, 400)
        else:
            print(f"[ERROR] Unknown action: {action}")
            return jsonify({"status": "error", "message": "Unknown action."}, 400)
    # GET: only when the user opens the page for the first time
    return render_template(
        "index.html",
        gestures=GESTURES,
        commands=COMMANDS,
        mappings=gesture_to_command,
        active=recognition_active,
        configs=config_files,
        selected_config=selected_config
    )

@app.route("/get_json_file", methods=["GET"])
def get_json_file() -> "Response":
    """
    Flask route to serve a JSON file from the static/configs directory.

    This route is used to load configuration files dynamically based on the request parameter 'file'.
    It ensures that the requested file exists and is a valid JSON file before serving it.
    Args:
        request (Flask request object): The request object containing query parameters.
    Returns:
        - JSON response with the content of the requested file if found.
        - 404 error if the file does not exist or is not a valid JSON file.
    """
    file_name = request.args.get("file") + ".json"  # Expecting a file name without path, e.g., "config1"
    if not file_name:
        return jsonify({"error": "File name not provided"}), 400

    # Ensure the file is in the correct directory and has a .json extension
    if not os.path.isfile(os.path.join(CONFIG_DIR, file_name)):
        return jsonify({"error": "File not found"}), 404

    with open(os.path.join(CONFIG_DIR, file_name), "r") as f:
        data = json.load(f)
    
    return jsonify(data)



# Global variables for gesture recognition state and process
# Recognition state
recognition_active = False

# Process for gesture recognition
# This will be set to None initially and will be started when the user clicks "Start Recognition".
# It will be a multiprocessing.Process that runs the start_gesture_recognition function
# with the necessary arguments.
# It will be set to None when the user clicks "Stop Recognition"
recognition_process = None

# Queue for webcam frames
# This queue will be used to send webcam frames from the gesture recognition process to flask_client.py
webcam_frame_queue = None

# Queue for recognized gestures
flask_to_web_interface_queue = None
# This queue will be used to send recognized gestures from gesture_recognizer.py to flask_client.py


@app.route("/start", methods=["GET"])
def start_recognition() -> "Response":
    """
    Starts the gesture recognition process if it is not already active.
    This endpoint initializes the necessary queues for inter-process communication and
    launches a separate process to handle gesture recognition. It sets the global
    `recognition_active` flag to True and starts the process with the required arguments.
    If the recognition process is already active, it does nothing.
    Args:
        None
    Returns:
        Response: A JSON response indicating the status and whether recognition is active.
    """

    global recognition_active, recognition_process

    if not recognition_active:
        recognition_active = True
        # Initialize queues for inter-process communication
        global webcam_frame_queue
        webcam_frame_queue = multiprocessing.Queue()
        global last_gesture
        last_gesture = multiprocessing.Array(ctypes.c_char, 30)
        # global flask_to_web_interface_queue
        # flask_to_web_interface_queue = multiprocessing.Queue()
        # Pass gesture_to_command as an argument
        global gesture_to_command
        global gesture_recognizer_to_socket_queue
        recognition_process = multiprocessing.Process(
            target=start_gesture_recognition,
            args=(gesture_to_command, webcam_frame_queue, gesture_recognizer_to_socket_queue, last_gesture,),
        )
        recognition_process.start()
        print("[INFO] Gesture recognition process started.")
    return jsonify({"status": "ok", "active": True})

@app.route("/stop", methods=["GET"])
def stop_recognition() -> "Response":
    """
    Stops the gesture recognition process if it is currently active.

    This endpoint is accessible via the "/stop" route. It checks if the gesture recognition process is active.
    If not active, it returns a JSON response indicating that recognition is not active.
    If active, it sets the recognition flag to False, terminates the recognition process if it is alive,
    closes and joins the webcam frame queue, and sets the process reference to None.
    Returns a JSON response indicating the recognition process has been stopped.
    Args:
        None
    Returns:
        Response: A Flask JSON response with the status and active state.
    """
    global recognition_active, recognition_process
    
    # Check if recognition is already inactive
    if recognition_active is False:
        return jsonify({"status": "no", "active": False})
    recognition_active = False
    
    # If the recognition process is still running, terminate it and its associated queues with flask_client.py
    if recognition_process and recognition_process.is_alive():
        recognition_process.terminate()
        print("[INFO] Stopping recognition...")
        global webcam_frame_queue
        webcam_frame_queue.close()
        webcam_frame_queue.join_thread()
        recognition_process = None
        print("[INFO] Gesture recognition process stopped.")

    return jsonify({"status": "ok", "active": False})

@app.route("/video_feed", methods=["GET"])
def video_feed() -> "Response":
    """
    Route that streams video frames from the server to the client as an MJPEG stream.
    Args:
        None
    Returns:
        Response: A Flask Response object that streams JPEG-encoded video frames
        using the multipart/x-mixed-replace MIME type.

    The video stream is generated by continuously retrieving frames from the
    `webcam_frame_queue` while `recognition_active` is True. Each frame is encoded
    as a JPEG image and sent as part of the HTTP response. The stream can be
    consumed by browsers or clients that support MJPEG streams.
    """
    def generate():
        print("[INFO] Starting video feed...")
        while recognition_active:
            frame = webcam_frame_queue.get() if webcam_frame_queue else None
            if frame is None:
                continue
            # Encode the frame as JPEG.
            # ret is True if the encoding was successful, buffer contains the encoded image.
            # If ret is False, we skip the frame and continue to the next iteration.
            # buffer is a numpy array containing the encoded image data.
            # We use cv2.imencode to convert the frame to JPEG format.
            # ret is a boolean indicating if the encoding was successful.
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            # b indicates that the string is a byte string.
            # Yield the frame in the format required for MJPEG streaming.
            # The frame is prefixed with the boundary string and headers.
            # The boundary string is used to separate different frames in the stream.
            # The frame is followed by a double CRLF sequence to indicate the end of the frame
            # The buffer is converted to bytes using the tobytes() method.
            # The CRLF sequence is used to separate different frames in the stream.
            # The yield statement sends the frame to the client as part of the HTTP response.
            # The response is sent as a multipart/x-mixed-replace stream.
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
    # Return a Flask Response object that streams the video feed.
    # MIME type tells the browser to expect a continuous stream of images, 
    # allowing it to display the video in real time.
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/stop_client", methods=["GET"])
def stop_client() -> "Response":
    """
    Flask route to stop the client application.
    This route is used to terminate the client process gracefully.
    It stops the gesture recognition process and returns a JSON response indicating success.
    Args:
        None
    Returns:
        Response: A JSON response indicating that the client has been stopped successfully.
    """
    global recognition_active
    if recognition_active:
        stop_recognition()
    os.kill(os.getpid(), signal.SIGINT)
    print("[INFO] Client process stopped.")
    return jsonify({"status": "ok", "message": "Client stopped successfully."})

@app.route("/check_server", methods=["GET"])
def check_server() -> "Response":
    """
    Flask route to check if the server is running.
    This route sends a request to the server and checks if it responds with a 200 OK status.
    If the server is reachable, it returns a JSON response indicating success.
    If the server is not reachable, it returns a JSON response indicating failure.
    Args:
        None
    Returns:
        Response: A JSON response indicating whether the server is running or not.
    """
    global server_is_running
    if server_is_running.value:
        print("[INFO] Server is running.")
        return jsonify({"status": "ok", "message": "Connection established."})
    else:
        print("[ERROR] Server is not running.")
        return jsonify({"status": "error", "message": "Server is not running."}), 503
    
@app.route("/get_recognized_gesture", methods=["GET"])
def send_recognized_gesture() -> "Response":
    """
    Retrieve the latest recognized gesture from the background recognizer.

    Attempts to pull a value from the global `flask_to_web_interface_queue` without blocking.
    - If the queue is not initialized, returns a 503 error.
    - If the queue is empty, returns `"gesture": null`.
    - If a gesture is available, returns it immediately.

    JSON response format (200 OK):
        {
            "status": "ok",
            "gesture": <string|null>
        }

    Error response (503 Service Unavailable):
        {
            "status": "error",
            "message": "Gesture recognizer process is not running."
        }
    """
    global recognition_active
    if recognition_active is False:
        print("[DEBUG] Recognition process is not active (send_recognized_gesture())")
        return jsonify({"status": "error", "message": "Gesture recognizer process is not running."}), 503
    global last_gesture
    print(f"[INFO] Sending recognized gesture ({last_gesture}) to web interface")
    # Legge la stringa dalla memoria condivisa
    raw_bytes = bytes(last_gesture[:]).rstrip(b'\x00')  # Rimuove zeri finali
    gesture = raw_bytes.decode()
    print(f"[INFO] Recognized gesture: {gesture} (flask_client.py)")
    return jsonify({"status": "ok", "message": gesture})