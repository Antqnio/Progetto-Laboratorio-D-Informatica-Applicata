## gesture_recognizer.py
# -*- coding: utf-8 -*-
"""
This module contains the function to start real-time gesture recognition using a webcam.
It uses MediaPipe for gesture recognition and OpenCV for webcam capture.
It processes video frames to recognize hand gestures and maps them to commands using a provided dictionary.
Recognized commands are sent to a server via a multiprocessing queue.
"""


import cv2
import mediapipe as mp
import numpy as np
import os
import time as tm
import multiprocessing
import signal
import sys
import torch
import torch.nn as nn
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from send_command_to_server import send_command_to_server
from client_constants import COMMANDS, GESTURES as class_names

def make_sigterm_handler(cap) -> "callable":
    """
    Creates a SIGTERM signal handler that safely releases a video capture device and closes OpenCV windows.
    This function is useful for ensuring that resources are cleaned up properly when the program receives a termination signal.
    A termination signal (SIGTERM) is sent by flask_client.py when the user wants to stop recognizing gestures.
    Args:
        cap: An object representing the video capture device (e.g., cv2.VideoCapture).
    Returns:
        callable: A signal handler function that can be registered to handle SIGTERM signals. When invoked, it releases the video capture device if open, destroys all OpenCV windows, and exits the program.
    Note:
        The returned handler function expects to be called with the standard signal handler arguments (signum, frame).
    """
    
    def handle_sigterm(signum, frame):
        print("[INFO] received SIGTERM.")
        if cap.isOpened():
            cap.release()
            print("[INFO] Webcam released.")
        cv2.destroyAllWindows()
        sys.exit(0)
    return handle_sigterm

def start_gesture_recognition(gesture_to_command: dict, webcam_queue: "multiprocessing.Queue", client_to_server_queue: "multiprocessing.Queue", last_gesture: "multiprocessing.Array") -> None:
    """
    Starts real-time gesture recognition using a webcam and sends associated commands to a server.
    This function initializes a MediaPipe gesture recognizer, captures video frames from the webcam,
    processes them to recognize hand gestures, and maps recognized gestures to commands using the
    provided `gesture_to_command` dictionary. Recognized commands are sent to the server via the
    `client_to_server_queue`. Captured frames are also placed into the `webcam_queue` for further use.
    Args:
        gesture_to_command (dict): A dictionary mapping gesture category names (str) to command strings. If None or empty, the gestures will be captured without sending commands to server
        webcam_queue (multiprocessing.Queue): Queue to send captured webcam frames to the Flask client.
        client_to_server_queue (multiprocessing.Queue): Queue to send recognized commands to the server.
        last_gesture (multiprocessing.Array): Last gesture recognized. This array will be used to communicate that last gesture to flask_client.py.
    Returns:
        None
    Raises:
        ValueError: If `gesture_to_command` is not provided or is empty.
    Notes:
        - Requires a compatible MediaPipe gesture recognition model file in the same directory.
        - Uses OpenCV for webcam capture and MediaPipe for gesture recognition.
        - The function runs an infinite loop until the user presses the 'q' key.
        - Only every 10th recognitions, the result is processed to reduce command spamming.
        - Prints information and debug messages to the console.
    """


    # Prepare the MediaPipe model path
    model_path = os.path.join(os.path.dirname(__file__), "handnet_two_hands.pth")
    
    # Model parameters
    num_classes = 19  # stesso valore usato nel training
    # Two hands → 21 landmarks × 3 coords × 2 = 126 inputs
    input_size   = 21 * 3 * 2
    hidden_size  = 128
    # Model
    class HandNet(nn.Module):
        def __init__(self, input_size=63, hidden_size=128, num_classes=19):
            super(HandNet, self).__init__()
            self.net = nn.Sequential(
                nn.Linear(input_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, num_classes)
        )
        def forward(self, x):
            return self.net(x)

    # Load model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = HandNet(input_size=input_size, hidden_size=hidden_size, num_classes=num_classes).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    print("[INFO] gesture_to_command: {}".format(gesture_to_command))
    
    # Separate Mediapipe hands for drawing landmarks on frame
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
    mp_draw = mp.solutions.drawing_utils
    
    # Shared state for visualization (not needed due to AJAX)
    # last_predicted = ""
    
    # Count the number of recognized gestures to reduce command spamming.
    # When the number of recognized gestures is a multiple of 10, the command is sent to the server.
    counter = 0

    def send_result(recognized_gesture: str) -> None:
        """
        Processes the gesture recognition result, sending recognized gesture commands to the server at specified intervals.
        Args:
            result (GestureRecognizerResult): The result object containing recognized gestures.
        Side Effects:
            - Increments a nonlocal counter to control the frequency of command sending.
            - Sends recognized gesture commands to the server via `client_to_server_queue` every 10th call.
            - Prints information about sent commands or lack of recognized gestures.
        Returns:
            None
        Notes:
            - Only gestures with a mapped command in `COMMANDS` are sent.
            - If no gestures are recognized, an informational message is printed.
        """
        def save_last_gesture(recognized_gesture) -> None:
            """
            Saves the latest recognized gesture into the shared memory buffer `last_gesture`.

            This function first clears the existing contents of the buffer by setting each byte to null (`\x00`),
            then writes the new gesture string byte by byte into the buffer.

            Args:
                recognized_gesture (str or bytes): The gesture to store. Can be a string or a bytes-like object.
            Returns:
                None
            """
            # Write the new gesture
            for i, char in enumerate(recognized_gesture):
                last_gesture[i] = char.encode() if isinstance(char, str) else char
            # Empty the remaining parts of the buffer
            for i in range(len(recognized_gesture), len(last_gesture)):
                last_gesture[i] = b'\x00'
                
        nonlocal counter
        counter += 1
        if counter % 10 != 0:
            return
        save_last_gesture(recognized_gesture)
        if gesture_to_command is None or not gesture_to_command:
            print(f"[INFO] gesture_to_command is empty. Sending recognized gesture ({recognized_gesture}) to flask_client.py...")
            return
        if gesture_to_command.get(recognized_gesture) is None:
            print(f"[INFO] Gesture '{recognized_gesture}' not mapped to any command.")
            return
        # Send the associated command to the send_command_to_server.py module:
        command = gesture_to_command.get(recognized_gesture)
        if command in COMMANDS:
            print(f"[INFO] Sending associated command: {command}")
            client_to_server_queue.put(command)
    

    # Select a webcam to capture video from.
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    # Register the SIGTERM signal handler to release the webcam and close OpenCV windows.
    signal.signal(signal.SIGTERM, make_sigterm_handler(cap))
    # Set the video codec, frame width, and height.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # cap.set(cv2.CAP_PROPFPS, 30)

    if not cap.isOpened():
        print("[INFO] Webcam is not opened. Please check your webcam connection.")
        return

    print("[INFO] Webcam opened correctly!")

    try:
        while True:
            # Record start time for FPS
            # start_time = tm.time()
            
            # Read a frame from the webcam.
            ret, frame = cap.read()
            # If the frame is not read correctly, print an error message and continue.
            if not ret:
                # Wait for a short time before trying to read the frame again.
                tm.sleep(0.1)
                continue
            
            # Put the frame into the webcam queue.
            # webcam_queue.put(frame.copy())

            # Convert the frame from OpenCV BGR format to RGB format.
            # MediaPipe uses RGB format for image processing.
            # OpenCV uses BGR format by default.
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb_frame)
            
           
            
            # Draw last predicted gesture text (not needed due to AJAX)
            # cv2.putText(frame, f'Gesture: {last_predicted}', (10, 30),
            #            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
             # --- 1) Decide recognized_gesture ---
            if not result.multi_hand_landmarks:
                # No hand → never run the model
                recognized_gesture = "None"
            else:
                # Build input feature vector of length 126
                feats = []
                # Collect landmarks for up to two hands
                for hand_landmarks in result.multi_hand_landmarks[:2]:
                    for lm in hand_landmarks.landmark:
                        feats.extend([lm.x, lm.y, lm.z])
                # If only one hand is detected, pad the second hand with zeros
                if len(result.multi_hand_landmarks) == 1:
                    feats.extend([0.0] * (21 * 3))
                # Draw landmarks on the frame
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Perform inference only when there is at least one hand
                x = torch.tensor(feats, dtype=torch.float32).unsqueeze(0).to(device)
                with torch.no_grad():
                    logits          = model(x)
                    pred_class      = logits.argmax(dim=1).item()
                    recognized_gesture = class_names[pred_class]
            print(f"[INFO] Recognized gesture: {recognized_gesture} (gesture_recognizer.py)")
            send_result(recognized_gesture)
            
            # Calculate and display FPS
            # end_time = tm.time()
            # fps = 1.0 / (end_time - start_time) if (end_time - start_time) > 0 else 0.0
            # cv2.putText(frame, f'FPS: {fps:.2f}', (10, 70),
            #            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Draw FPS using JetBrains Mono font via PIL for custom font support
            # try:
            #     from PIL import Image, ImageDraw, ImageFont
            #     # Convert to PIL image
            #     pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            #     draw = ImageDraw.Draw(pil_img)
            #     # Load the JetBrains Mono font (ensure the .ttf file is in working directory)
            #     font = ImageFont.truetype('JetBrainsMono-Regular.ttf', 20)
            #     # Position at top-left corner (x=10, y=10)
            #     draw.text((10, 10), f'FPS: {fps:.2f}', font=font, fill=(255, 0, 0))
            #     # Convert back to OpenCV image
            #     frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            # except Exception as e:
            #     # Fallback to default font if PIL or TTF not available
            #     cv2.putText(frame, f'FPS: {fps:.2f}', (10, 20),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            #     # Optionally log the error
            #     # print(f"Font fallback due to: {e}")
            
            
            # Send processed frame (with overlays) to queue for web interface
            webcam_queue.put(frame.copy())
            
            # Break the loop and release the webcam if the user presses the 'q' key.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # Release the webcam and close all OpenCV windows.
        cap.release()
        # Wait for a short time to ensure the webcam is released properly.
        tm.sleep(0.1)
        cv2.destroyAllWindows()
