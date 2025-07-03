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
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from send_command_to_server import send_command_to_server
from client_constants import COMMANDS

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

def start_gesture_recognition(gesture_to_command: dict, webcam_queue: "multiprocessing.Queue" = None, client_to_server_queue: "multiprocessing.Queue" = None) -> None:
    """
    Starts real-time gesture recognition using a webcam and sends associated commands to a server.
    This function initializes a MediaPipe gesture recognizer, captures video frames from the webcam,
    processes them to recognize hand gestures, and maps recognized gestures to commands using the
    provided `gesture_to_command` dictionary. Recognized commands are sent to the server via the
    `client_to_server_queue`. Captured frames are also placed into the `webcam_queue` for further use.
    Args:
        gesture_to_command (dict): A dictionary mapping gesture category names (str) to command strings.
        webcam_queue (multiprocessing.Queue, optional): Queue to send captured webcam frames. Defaults to None.
        client_to_server_queue (multiprocessing.Queue, optional): Queue to send recognized commands to the server. Defaults to None.
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
    model_path = os.path.join(os.path.dirname(__file__), "gesture_recognizer.task")
    
    # Initialize MediaPipe tasks and options
    BaseOptions = mp.tasks.BaseOptions
    GestureRecognizer = mp.tasks.vision.GestureRecognizer
    GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
    GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
    VisionRunningMode = mp.tasks.vision.RunningMode

    print("[INFO] gesture_to_command: {}".format(gesture_to_command))
    
    # Count the number of recognized gestures to reduce command spamming.
    # When the number of recognized gestures is a multiple of 10, the command is sent to the server.
    counter = 0

    def get_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int) -> None:
        """
        Processes the gesture recognition result, sending recognized gesture commands to the server at specified intervals.
        Args:
            result (GestureRecognizerResult): The result object containing recognized gestures.
            output_image (mp.Image): The output image associated with the recognition (unused in this function).
            timestamp_ms (int): The timestamp in milliseconds when the result was produced.
        Side Effects:
            - Increments a nonlocal counter to control the frequency of command sending.
            - Sends recognized gesture commands to the server via `client_to_server_queue` every 10th call.
            - Prints information about sent commands or lack of recognized gestures.
        Raises:
            ValueError: If `gesture_to_command` is not provided or is empty.
        Returns:
            None
        Notes:
            - Only gestures with a mapped command in `COMMANDS` are sent.
            - If no gestures are recognized, an informational message is printed.
        """
        if gesture_to_command is None or not gesture_to_command:
            raise ValueError("gesture_to_command must be provided and cannot be empty.")
        nonlocal counter
        counter += 1
        if counter % 10 != 0:
            return
        # Print all recognized category_names:
        for gesture_list in result.gestures:
            for classification in gesture_list:
                if classification.category_name is not None:
                    if gesture_to_command.get(classification.category_name) is None:
                        print(f"[INFO] Gesture '{classification.category_name}' not mapped to any command.")
                        continue
                    # Send the recognized gesture to the server:
                    command = gesture_to_command.get(classification.category_name)
                    if command in COMMANDS:
                        print(f"[INFO] Sending associated command: {command}")
                        client_to_server_queue.put(command)
        # If there are no gestures recognized, print a message:
        if not result.gestures:
            print("[INFO] No gesture recognized")

    # Create the GestureRecognizerOptions with the model path and result callback.
    # The result callback is called every time a gesture is recognized.
    # The running mode is set to LIVE_STREAM to process frames from the webcam.
    # The number of hands is set to 2 to recognize gestures from both hands.
    # The model asset path is set to the path of the gesture recognizer model file.
    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=get_result,
        num_hands=2
    )

    with GestureRecognizer.create_from_options(options) as recognizer:
        # Select a webcam to capture video from.
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
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

                # Read a frame from the webcam.
                ret, frame = cap.read()
                # If the frame is not read correctly, print an error message and continue.
                if not ret:
                    # Wait for a short time before trying to read the frame again.
                    tm.sleep(0.1)
                    continue
                
                # Put the frame into the webcam queue.
                webcam_queue.put(frame.copy())

                # Convert the frame from OpenCV BGR format to RGB format.
                # MediaPipe uses RGB format for image processing.
                # OpenCV uses BGR format by default.
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert the frame from OpenCV to a numpy array.
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                # Send live image data to perform gesture recognition.
                # The results are accessible via the `result_callback` provided in
                # the `GestureRecognizerOptions` object.
                # The gesture recognizer must be created with the live stream mode.
                # The frame timestamp is calculated in milliseconds.
                # This is used to synchronize the frames with the results.
                # The timestamp is calculated using the OpenCV tick count and tick frequency.
                # This is necessary to ensure that the results are processed in the correct order.
                # The timestamp is used to synchronize the frames with the results.
                frame_timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)
                # Call the recognizer to process the image and recognize gestures.
                # The recognizer will call the `get_result` function with the recognized gestures.
                recognizer.recognize_async(mp_image, frame_timestamp_ms)
                
                # Break the loop and release the webcam if the user presses the 'q' key.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            # Release the webcam and close all OpenCV windows.
            cap.release()
            # Wait for a short time to ensure the webcam is released properly.
            tm.sleep(0.1)
            cv2.destroyAllWindows()
