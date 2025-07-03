# client/main.py

import multiprocessing
from send_command_to_server import send_command_to_server
import flask_client
import ctypes

def main():
    """
    Main entry point for the client application.
    - Sets the multiprocessing start method to 'spawn' for clean child process creation.
    - Initializes a single multiprocessing queue for communication between client and server.
    - Starts a separate process to listen to the queue and send commands to the server.
    - Attaches the queue to the Flask client for global access.
    - Runs the Flask application to handle incoming HTTP requests.
    - On Flask shutdown, signals the command-sending process to terminate and waits for it to finish.
    Args:
        None
    Returns:
        None
    Notes:
        - This function is designed to be run as the main module of the client application.
        - It uses the Flask framework to create a web client that communicates with a server.
        - The multiprocessing module is used to handle command sending in a separate process.
        - The Flask app runs in threaded mode to handle multiple HTTP requests concurrently.
    """
    # Set the start method for multiprocessing to 'spawn'
    multiprocessing.set_start_method("spawn", force=True)

    # Initialize a single multiprocessing queue for communication between gesture_recognizer.py and send_command_to_server.py
    gesture_recognizer_to_socket_queue = multiprocessing.Queue()
    flask_client.gesture_recognizer_to_socket_queue = gesture_recognizer_to_socket_queue
    
    # Initialize a single multiprocessing queue for communication between Flask client and send_command_to_server.py
    server_is_running = multiprocessing.Value(ctypes.c_bool, True)  # Shared boolean
    flask_client.server_is_running = server_is_running
    
    # Start a separate process to listen to the queue and send commands to the server
    send_proc = multiprocessing.Process(
        target=send_command_to_server,
        args=(gesture_recognizer_to_socket_queue, server_is_running,)
    )
    send_proc.start()


    # Start Flask (this blocks until you stop it with CTRL-C)
    flask_client.app.run(host="0.0.0.0", port=8080, threaded=True)
    print("[INFO] Flask client started.")

    # When Flask stops, signal the command-sending process to terminate
    print("[INFO] Stopping client process...")
    send_proc.terminate()
    print("[INFO] Waiting for command-sending process to finish...")
    send_proc.join()
    print("[INFO] Client processes stopped.")

if __name__ == "__main__":
    main()
