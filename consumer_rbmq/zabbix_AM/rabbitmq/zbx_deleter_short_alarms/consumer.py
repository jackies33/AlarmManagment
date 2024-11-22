



"""
Example to create docker-compose container

sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

sudo curl -L "https://github.com/docker/compose/releases/download/$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

docker --version
docker-compose --version

mcedit Dockerfile:

_________________
FROM python:3.9-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    musl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "consumer.py"]
_________________


add all app files in derectory with Dockerfile

mcedit requirements.txt
_________________
pika==1.2.0
requests==2.26.0
fastapi
uvicorn
pyzabbix
_________________
docker build -t myapp:latest .
.

mcedit docker-compose.yml

_________________
version: '3.8'

services:
  zabbix_deleter_short_alarms:
    build: .
    container_name: zabbix_deleter_short_alarms
    environment:
      - RABBITMQ_HOST=10.50.174.38
    networks:
      - app-network
    ports:
      - "8057:8057"

networks:
  app-network:
    driver: bridge
_________________

docker-compose build --no-cache
docker-compose up -d
docker ps

"""


import time
import pika
import json
import threading
import logging
from fastapi import FastAPI
import uvicorn
from concurrent.futures import ThreadPoolExecutor

from my_env import rabbitmq_host, rbq_producer_pass, rbq_producer_login, rbq_queue_for_deleter, server_port
import zbx_deleter

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)


executor = ThreadPoolExecutor(max_workers=20)

def process_message(queue_name, message_body):
    try:
        message = json.loads(message_body)
        logger.info(f"Received message from {queue_name}: {message}")
    except json.JSONDecodeError:
        message = message_body
        logger.warning(f"Failed to decode JSON from {queue_name}: {message_body}")

    executor.submit(zbx_deleter.zbx_deleter_trigger_with_delay, message)


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
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback, auto_ack=False)

        logger.info(f"Start listening on queue: {queue_name}")
        #print(f"Start listening: {queue_name}")
        channel.start_consuming()

    except Exception as e:
        logger.error(f"Error connecting to RabbitMQ {queue_name}: {e}", exc_info=True)


def start_consumer(queue_name):
    while True:
        try:
            consume_from_rabbitmq(queue_name)
        except pika.exceptions.AMQPConnectionError:
            logger.error(f"Connection lost with RabbitMQ {queue_name}. Reconnecting...")
            time.sleep(3)
        except Exception:
            logger.error(f"Connection lost with RabbitMQ {queue_name}. Reconnecting...")
            time.sleep(3)

def run_webserver():
    logger.info("Starting webserver...")
    uvicorn.run(app, host="0.0.0.0", port=server_port)


def start_threads(queue_name):
    webserver_thread = threading.Thread(target=run_webserver, daemon=True)
    webserver_thread.start()
    consumer_thread = threading.Thread(target=start_consumer, args=(queue_name,), daemon=True)
    consumer_thread.start()
    webserver_thread.join()
    consumer_thread.join()


if __name__ == "__main__":
    logger.info("Starting application...")
    start_threads(rbq_queue_for_deleter)




