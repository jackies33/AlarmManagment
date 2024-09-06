




import time
import pika
import json


#sys.path.append('/opt/zabbix_custom/zabbix_AM/')

from my_env import rabbitmq_host, rbq_producer_pass, rbq_producer_login, rbq_queue_for_sender
import zbx_sender

def process_message(queue_name, message_body):
    try:
        try:
            message = json.loads(message_body)
        except Exception as err:
            message = message_body
        #message_logger.info(f"Processing message from {queue_name}: {message}")
        #print(f"Processing message from {queue_name}: {message}")
        result = zbx_sender.prepare_data_to_zabbix(message)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from queue {queue_name}: {e}")
        #logger.error(f"Failed to decode JSON from queue {queue_name}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        #logger.error(f"An unexpected error occurred: {e}")


def on_message_callback(ch, method, properties, body):
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
        channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback, auto_ack=True)
        print(f"Start listening: {queue_name}")
        channel.start_consuming()

    except Exception as e:
        print(f"Error connection to RabbitMQ {queue_name}: {e}")

def start_consumer(queue_name):
    while True:
        try:
            consume_from_rabbitmq(queue_name)
        except pika.exceptions.AMQPConnectionError:
            print(f"Connection lost with RabbitMQ {queue_name}. Reconection...")
            time.sleep(3)

if __name__ == "__main__":
    start_consumer(rbq_queue_for_sender)



