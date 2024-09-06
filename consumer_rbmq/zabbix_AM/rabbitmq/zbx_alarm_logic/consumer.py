
import pika
import json
import logging
import requests
import threading
import time

from my_env import rabbitmq_host, rbq_producer_pass, rbq_producer_login
from zbx_alarm import alert_logic

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

active_consumers = {}

def get_alarm_queues():
    try:
        api_url = f"http://{rabbitmq_host}:15672/api/queues"
        response = requests.get(api_url, auth=(rbq_producer_login, rbq_producer_pass))
        response.raise_for_status()
        queues = response.json()
        alarm_queues = [queue['name'] for queue in queues if queue['name'].startswith('alarm')]
        return alarm_queues
    except requests.RequestException as e:
        print(f"Failed to get queues from RabbitMQ: {e}")
        return []

def process_message(queue_name, message_body):
    try:
        message = json.loads(message_body)
        logger.info(f"Received message from {queue_name}: {message}")
        alert_logic(queue_name, message)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to decode JSON from {queue_name}: {message_body}")
    except Exception as e:
        logger.warning(f"An unexpected error occurred: {e}")

def on_message_callback(ch, method, properties, body):
    logger.info(f"Processing message from queue: {method.routing_key}")
    process_message(method.routing_key, body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_from_rabbitmq(queue_name):
    try:
        credentials = pika.PlainCredentials(rbq_producer_login, rbq_producer_pass)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=rabbitmq_host,
            credentials=credentials
        ))
        channel = connection.channel()
        channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback, auto_ack=False)
        logger.info(f"Start listening on queue: {queue_name}")
        channel.start_consuming()

    except Exception as e:
        logger.error(f"Error connecting to RabbitMQ {queue_name}: {e}", exc_info=True)

def consumer_core():
    global active_consumers

    while True:
        alarm_queues = get_alarm_queues()
        if not alarm_queues:
            print("No alarm queues found.")
            time.sleep(5)
            continue
        try:
            for queue in alarm_queues:
                if queue not in active_consumers:
                    thread = threading.Thread(target=consume_from_rabbitmq, args=(queue,))
                    thread.daemon = True
                    thread.start()
                    active_consumers[queue] = thread
            time.sleep(60)
        except Exception as err:
            logger.error(f"error in consumer core, trying again...")

if __name__ == "__main__":
    consumer_core()

