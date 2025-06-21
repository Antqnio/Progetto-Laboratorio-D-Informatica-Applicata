import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

model_path = './gesture_recognizer.task'

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode

# Create a gesture recognizer instance with the live stream mode:
def print_result(result: GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    print('gesture recognition result:  {}'.format(result))

options = GestureRecognizerOptions(
    base_options = BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result,
    num_hands=2)
with GestureRecognizer.create_from_options(options) as recognizer:
    # The detector is initialized. Use it here.
    # ...
    # Use OpenCV’s VideoCapture to start capturing from the webcam.
    
    # Select a webcam to capture video from.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Webcam non accessibile")
        exit()

    print("Webcam aperta correttamente!")
    # Create a loop to read the latest frame from the camera using VideoCapture#read()
    while True:
        
        # Read a frame from the webcam.
        ret, frame = cap.read()
        if not ret:
            continue # Or break if you want to stop on failure.
        # Show the frame in a window using OpenCV’s imshow() function.
        cv2.imshow("Webcam", frame)
        # Convert the frame from OpenCV to a numpy array.
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        # Send live image data to perform gesture recognition.
        # The results are accessible via the `result_callback` provided in
        # the `GestureRecognizerOptions` object.
        # The gesture recognizer must be created with the live stream mode.
        recognizer.recognize_async(mp_image, frame_timestamp_ms)
        # Break the loop and release the webcam if the user presses the 'q' key.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            break
    
    

# Codice webcam
"""
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Webcam non accessibile")
    exit()

print("Webcam aperta correttamente!")

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=numpy_frame_from_opencv)
    
    risultato_riconoscimento = recognizer.recognize_async(mp_image, frame_timestamp_ms)
    top_gesture = risultato_riconoscimento.gestures[0][0]
    hand_landmarks = risultato_riconoscimento.hand_landmarks
    frame_elaborato = frame.__deepcopy__()
    cv2.imshow("Webcam", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
"""
