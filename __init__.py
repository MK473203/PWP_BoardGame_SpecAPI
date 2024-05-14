import requests
import threading
import atexit
import os
from flask import Flask

workers = []

BOARDGAME_SERVER = "http://localhost:5000"
GAMES_HREF = None
MASON = "application/vnd.mason+json"

RABBITMQ_BROKER_URL = "amqp://guest:guest@localhost:5672/%2F?connection_attempts=3&heartbeat=3600"

exit = threading.Event()

def cleaner_thread_function():
    global workers
    while not exit.is_set():
        exit.wait(60)
        for worker, thread in workers:
            if worker.connection.is_closed:
                thread.join()
    print("Cleaner thread shut down successfully", flush=True)

def create_app(test_config=None):
    

    global GAMES_HREF
    cleaner_thread = threading.Thread(
        target=cleaner_thread_function, name="Cleaner thread")
    app = Flask(__name__)

    import signal
    def quit(signo = None, _frame = None):
        exit.set()
        cleaner_thread.join()
        for worker, thread in workers:
            worker.close()
            thread.join()
        os.kill(os.getpid(), signal.SIGINT)
        

    for sig in ('TERM', 'INT'):
        signal.signal(getattr(signal, 'SIG' + sig), quit)


    try:
        resp = requests.get(BOARDGAME_SERVER + "/api/", timeout=10)
    except requests.Timeout:
        print("Could not get response from server")
        return

    GAMES_HREF = resp.json()["@controls"]["boardgame:games-all"]["href"]

    cleaner_thread.start()

    from . import specAPI

    app.register_blueprint(specAPI.api_bp)
    
    return app
