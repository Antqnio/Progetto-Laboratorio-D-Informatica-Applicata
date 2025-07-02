# client/main.py
import multiprocessing
from send_command_to_server import send_command_to_server
import flask_client
def main():
    # scegli 'spawn' per avere un caricamento pulito in child process
    multiprocessing.set_start_method("spawn", force=True)

    # inizializza la queue **una sola volta** a livello di main
    client_to_server_queue = multiprocessing.Queue()

    # avvia il processo che ascolta la queue e manda i comandi al server
    send_proc = multiprocessing.Process(
        target=send_command_to_server,
        args=(client_to_server_queue,)
    )
    send_proc.start()

    # aggancia la queue globale di app.py
    # (sovrascrive il valore None impostato in app.py)
    
    flask_client.client_to_server_queue = client_to_server_queue

    # avvia Flask (questo blocca finché non interrompi con CTRL‑C)
    flask_client.app.run(debug=True, host="0.0.0.0", port=8080, threaded=True)

    # quando Flask si ferma, diciamo al process di chiudersi
    client_to_server_queue.put(None)
    send_proc.join()

if __name__ == "__main__":
    main()
