import json
import requests
import time
from datetime import datetime
import json
import pika
from flask import Flask, Response
from flask.cli import with_appcontext
from flask_caching import Cache
from flask_restful import Resource, Api
from jsonschema import validate, ValidationError, draft7_format_checker
from werkzeug.exceptions import UnsupportedMediaType, NotFound, Conflict, BadRequest
from werkzeug.routing import BaseConverter


BOARDGAME_SERVER = "http://localhost:5000"
MASON = "application/vnd.mason+json"

RABBITMQ_BROKER_URL = "amqp://guest:guest@localhost:5672/%2F?connection_attempts=3&heartbeat=3600"

app = Flask(__name__)

workers = []


"""
Overall system schema:

- One worker and exchange per game instance
- One queue per spectator
- Exchange name is the game uuid
- Queue name is randomly generated by the spectating client

"""

class SpectatorWorker():

    def __init__(self, game_uuid: str):
        self.game_uuid = game_uuid
        self.game_url = BOARDGAME_SERVER + "/api/games/" + game_uuid

        resp = requests.get(self.game_url)

        if resp.status_code == 200:
            self.game_json = resp.json()
            self.game_found = True
        else:
            self.game_json = None
            self.game_found = False

    def get_game_info(self):
        for i in range(5):
            resp = requests.get(self.game_url)
            print(resp.status_code)
            print(resp.json())
            time.sleep(1)

    def log(self, message):
        print("Worker " + self.game_uuid[0:5] + ": " + message)

    def on_open(self, connection):
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.game_uuid,
            exchange_type="fanout"
        )

    def on_close(self, connection, exception):
        connection.ioloop.stop()

    def run(self):
        self.connection = pika.SelectConnection(pika.URLParameters(RABBITMQ_BROKER_URL),
                                                on_open_callback=self.on_open,
                                                on_close_callback=self.on_close)


@app.route("/spectate/<string:game>")
def spectate_game(game):
    global workers

    for worker in workers:
        if worker.game_uuid == game:


    worker = SpectatorWorker(game)
    if worker.game_found:
        worker.run()
        workers.append(worker)

        resp = {}
        resp["exchange"] = worker.game_uuid
        resp["@controls"]["amqp-url"] = RABBITMQ_BROKER_URL

        return Response(response=json.dumps(resp), status=200, mimetype=MASON)
    else:
        resp = {}
        resp["status"] = "Game was not found"

        return Response(response=json.dumps(resp), status=200, mimetype=MASON)


if __name__ == "__main__":
    app.run(port=5001)
