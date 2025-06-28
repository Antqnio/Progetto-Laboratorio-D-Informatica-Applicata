import cv2
import mediapipe as mp
import numpy as np
import os
import time as tm
import threading
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Variabile globale per esporre il frame alla Flask app
last_frame = None

def start_gesture_recognition(gesture_to_command: dict):
    """
    Starts the gesture recognizer using MediaPipe.
    This function initializes the gesture recognizer and starts capturing video from the webcam.
    It processes the video frames to recognize gestures in real-time.
    """

    model_path = os.path.join(os.path.dirname(__file__), "gesture_recognizer.task")

    BaseOptions = mp.tasks.BaseOptions
    GestureRecognizer = mp.tasks.vision.GestureRecognizer
    GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
    GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
    VisionRunningMode = mp.tasks.vision.RunningMode



    def get_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        from app.app import send_result
        for gesture_list in result.gestures:
            for classification in gesture_list:
                if classification.category_name is not None:
                    send_result(classification.category_name, gesture_to_command=gesture_to_command)
        if not result.gestures:
            print("No gesture recognized")

    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=get_result,
        num_hands=2
    )

    with GestureRecognizer.create_from_options(options) as recognizer:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print("Webcam non accessibile")
            return

        print("Webcam aperta correttamente!")

        try:
            last_exec = 0
            global last_frame
            while True:
                ret, frame = cap.read()
                if not ret:
                    tm.sleep(0.1)
                    continue

                last_frame = frame.copy()

                current_time = tm.time()
                if current_time - last_exec >= 1.0:
                    last_exec = current_time
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    
                    # Send live image data to perform gesture recognition.
                    # The results are accessible via the `result_callback` provided in
                    # the `GestureRecognizerOptions` object.
                    # The gesture recognizer must be created with the live stream mode.
                    frame_timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)
                    recognizer.recognize_async(mp_image, frame_timestamp_ms)
                
                # Break the loop and release the webcam if the user presses the 'q' key.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            tm.sleep(0.1)
            cv2.destroyAllWindows()
