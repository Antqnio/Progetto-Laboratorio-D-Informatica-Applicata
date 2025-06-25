from flask import Flask, render_template, request, redirect, url_for
import socket
import threading

app = Flask(__name__)

SERVER_IP = '192.168.1.105'  # IP del server TCP su Windows
SERVER_PORT = 9000

GESTURES = ["Thumbs Up", "Thumbs Down", "Open Palm", "Closed Fist", "Victory", "Gang", "Pointing Up"]
gesture_to_command = {}
recognition_active = False

def invia_comando_al_server(comando: str):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            s.sendall(comando.encode())
    except Exception as e:
        print(f"[Errore] Connessione al server fallita: {e}")

def riconoscimento_gesti():
    # Da sistemare
    comando = gesture_to_command.get(gesto_riconosciuto)
    if comando:
        print(f"[INFO] Invio comando associato: {comando}")
        invia_comando_al_server(comando)

@app.route("/", methods=["GET", "POST"])
def index():
    global gesture_to_command
    if request.method == "POST":
        for gesture in GESTURES:
            command = request.form.get(gesture)
            if command is not None:
                gesture_to_command[gesture] = command
        return redirect(url_for("index"))
    return render_template("index.html", gestures=GESTURES, mappings=gesture_to_command, active=recognition_active)

@app.route("/start")
def start_recognition():
    global recognition_active
    if not recognition_active:
        recognition_active = True
        threading.Thread(target=riconoscimento_gesti, daemon=True).start()
    return redirect(url_for("index"))

@app.route("/stop")
def stop_recognition():
    global recognition_active
    recognition_active = False
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
