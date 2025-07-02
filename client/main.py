# client/main.py

import multiprocessing
from send_command_to_server import send_command_to_server
import flask_client

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

    # Initialize a single multiprocessing queue for communication between client and server
    client_to_server_queue = multiprocessing.Queue()

    # Start a separate process to listen to the queue and send commands to the server
    send_proc = multiprocessing.Process(
        target=send_command_to_server,
        args=(client_to_server_queue,)
    )
    send_proc.start()


    # Bind the global queue from app.py to the Flask client
    # (this overrides the None value set in app.py)
    
    flask_client.client_to_server_queue = client_to_server_queue

    # Start Flask (this blocks until you stop it with CTRL-C)
    flask_client.app.run(debug=True, host="0.0.0.0", port=8080, threaded=True)


    # When Flask stops, signal the command-sending process to terminate
    client_to_server_queue.put(None)
    send_proc.join()

if __name__ == "__main__":
    main()
