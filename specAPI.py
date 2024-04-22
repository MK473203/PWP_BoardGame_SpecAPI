import json
import requests
from datetime import datetime
import json
import pika
from flask import Flask, Response, request
from flask.cli import with_appcontext
from flask_caching import Cache
from flask_restful import Resource, Api
from jsonschema import validate, ValidationError, draft7_format_checker
from werkzeug.exceptions import UnsupportedMediaType, NotFound, Conflict, BadRequest
from werkzeug.routing import BaseConverter


BOARDGAME_SERVER = "http://localhost:5000"
LINK_RELATIONS = "/api/link-relations/"

app = Flask(__name__)
app.config["RABBITMQ_BROKER_ADDR"] = "localhost"

class SpectatorWorker():
	def log_error(channel, message):
		channel.basic_publish(
			exchange="logs",
			routing_key="",
			body=json.dumps({
				"timestamp": datetime.now().isoformat(),
				"content": message
			})
		)


	def handle_task(channel, method, properties, body):
		print("Handling task")
		try:
			# try to parse data and return address from the message body
			task = json.loads(body)
			data = task["data"]
			sensor = task["sensor"]
			href = BOARDGAME_SERVER + task["@controls"]["edit"]["href"]
		except (KeyError, json.JSONDecodeError) as e:
			log_error(f"Task parse error: {e}")
		else:
			# calculate stats
			stats = calculate_stats(task["data"])
			stats["generated"] = datetime.now().isoformat()

			# send the results back to the API
			with requests.Session() as session:
				resp = session.put(
					href,
					json=stats
				)

			if resp.status_code != 204:
				# log error
				log_error(f"Unable to send result")
			else:
				channel.basic_publish(
					exchange="notifications",
					routing_key="",
					body=json
				)
		finally:
			# acknowledge the task regardless of outcome
			print("Task handled")
			channel.basic_ack(delivery_tag=method.delivery_tag)
        

@app.route("/start-spectate/")
