import requests
import json
import pika

API_URL = "http://localhost:5000"


if __name__ == "__main__":  # pragma: no cover

    def notification_handler(ch, method, properties, body):
        print(body)
        
    resp = requests.get(API_URL + "/api/games/")

    game = resp.json()["items"][0]

    print("trying to spectate game " + game["id"])

    resp = requests.get(API_URL + game["@controls"]["self"]["href"])

    game = resp.json()
    print(game["@controls"]["boardgame:spectate"]["href"])

    resp = requests.get(game["@controls"]["boardgame:spectate"]["href"])

    RABBITMQ_EXCHANGE = resp.json()["exchange"]
    RABBITMQ_BROKER_URL = resp.json()["@controls"]["amqp-url"]

    print(RABBITMQ_EXCHANGE)
    print(RABBITMQ_BROKER_URL)

    print("create connection")
    connection = pika.BlockingConnection(
        pika.URLParameters(RABBITMQ_BROKER_URL))
    channel = connection.channel()
    channel.exchange_declare(
        exchange=RABBITMQ_EXCHANGE,
        exchange_type="fanout"
    )
    result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
    channel.queue_bind(
        exchange=RABBITMQ_EXCHANGE,
        queue=result.method.queue
    )
    channel.basic_consume(
        queue=result.method.queue,
        on_message_callback=notification_handler,
        auto_ack=True
    )
    print("start consuming")
    channel.start_consuming()
