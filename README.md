# Progetto-Laboratorio-D-Informatica-Applicata

## Overview

This project implements a client-server system for gesture recognition using a webcam, allowing users to bind hand gestures to system commands (such as volume control, opening applications, screenshots, etc.).  
The web interface lets you configure gesture-command mappings, manage multiple configurations, and view the live webcam feed.

## Project Structure
```
.
├── client/                         # Client application (Flask + JS + HTML/CSS)
│   ├── main.py                     # Flask server entry point
│   ├── flask_client.py             # Flask backend logic
│   ├── send_command_to_server.py   # Sends commands to the TCP server
│   ├── src/gesture_recognizer/     # Gesture recognition module
│   ├── static/                     # Static files (JS, CSS, images)
│   └── templates/                  # HTML templates (index.html)
├── server/                         # TCP server for system command execution
│   ├── server.py                   # TCP server logic
│   └── server_requirements.txt
├── statistics/                     # Notebooks for statistics and analysis
├── start_client.sh                 # Script to start the client (Linux/Mac/WSL)
├── start_server.ps1                # Script to start the server (Windows PowerShell)
├── webcam_enable.ps1               # Script to enable webcam in WSL
├── .devcontainer/                  # Devcontainer configuration for VS Code
└── README.md
```
## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (for virtual environment and dependency management)
- VSCode and Dev Containers extension (ms-vscode-remote.remote-containers)
- Windows (for the server, which uses Windows system APIs)
- Working webcam (see WSL notes below)

## Installation and Usage
1. Clone the repo https://github.com/Antqnio/Progetto-Laboratorio-D-Informatica-Applicata.git on WSL.
2. Move the server folder into your Windows machine.
### Server (Windows)

1. Open PowerShell in the project folder.
2. Run:

   ```powershell
   .\start_server.ps1
   ```

   This script:
   - Creates a .venv virtual environment if it doesn't exist
   - Installs dependencies from server_requirements.txt
   - Starts the TCP server (server.py)

### Client (Linux/Mac/WSL)

1. Open VSCode.
2. Run the Dev Containers: Open Folder in Container... command and select the local folder - you can do so by clicking on the dialog window in the right corner of the screen or by opening the command palette (CTRL + SHIFT + P) and searching for it.
2. Run:

   ```sh
   ./start_client.sh
   ```

   This script:
   - Changes directory to client
   - Sets the `PYTHONPATH`
   - Starts the Flask server (main.py)

3. Open your browser at [http://localhost:8080](http://localhost:8080)

#### Webcam Access in WSL

To enable webcam access in WSL, you need to install and use `usbipd` via Windows PowerShell:

```powershell
wsl --update
winget install usbipd
usbipd list
usbipd attach --busid <your-busid> --wsl
```
Where \<your-busid> is the id of your webcam.  
You can automate this process by running webcam_enable.ps1.  
If successful, you should see a file named `video0` with `ls -l /dev/video0` in WSL.

##### **Webcam Troubleshooting**
If you get an opecv error while running the client or you can't see the webcam feed it might be that gesture_recognizer.py is trying to capture frames with a resolution and a video format which are not supported by your webcam.

##### ***Possible solution***  
In the file `gesture_recognizer.py`, you will find the following three lines of code:

```python
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
```

These lines set the video frame format and resolution for the webcam. If you select a format or resolution that is not supported by your specific webcam, OpenCV may fail to capture video or the webcam may not work at all.  
If your webcam does not work out of the box, you should try changing the format and resolution in these lines to values that are supported by your device.   
By default, we use the MJPEG format and a resolution of 640x480, which are commonly supported by most webcams.

## Main Features

- **Gesture-Command Configuration:** Bind gestures to system commands via the web UI.
- **Configuration Management:** Save, apply, and select different gesture-command configurations.
- **Recognizer Control:** Start/stop the gesture recognizer from the UI.
- **Live Webcam Feed:** See real-time video for gesture input.
- **Supported Commands:** Volume control, open calculator, Task Manager, screenshot, Alt+Tab, Play/Pause, mouse scroll.
- **Supported Gestures**:
    - Thumb Up (👍)
    - Thumb Down (👎)
    - Open Palm (🖐️)
    - Closed Fist (✊)
    - Victory (✌️)
    - I Love You (🤟)
    - Pointing Up (👆)

## Authors

- Alessandro Trusendi
- Antonio Querci

## License

Educational project for "Laboratorio D'Informatica Applicata", July 2025.
