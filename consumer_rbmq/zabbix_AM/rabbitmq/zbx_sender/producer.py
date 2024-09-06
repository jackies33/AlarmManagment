


import pika
import logging

from my_env import rabbitmq_host, rbq_producer_pass, rbq_producer_login, rbq_producer_exchange,rbq_producer_route_key



#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def rb_producer(message):
    credentials = pika.PlainCredentials(rbq_producer_login, rbq_producer_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host,credentials=credentials))
    channel = connection.channel()
    channel.basic_publish(
        exchange=rbq_producer_exchange,
        routing_key=rbq_producer_route_key,
        body=message
    )
    #logging.info(f"CHANNEL!!!! : {channel}")
    #logging.info(f"CONNECTION@@@@ : {connection}")
    connection.close()



