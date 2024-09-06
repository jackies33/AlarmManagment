



"""
Example to create docker-compose container



mkdir -p /opt/rabbitmq_logs
chmod 777 /opt/rabbitmq_logs



sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

sudo curl -L "https://github.com/docker/compose/releases/download/$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

docker --version
docker-compose --version

mcedit Dockerfile

_________________
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
_________________


add all app files in derectory with Dockerfile

mcedit requirements.txt
_________________
fastapi
uvicorn
pika
requests
pyzabbix
_________________
docker build -t myapp:latest .

mcedit docker-compose.yml

_________________
version: '3.8'

services:
  zbx_alarm_logic:
    build: .
    container_name: zbx_alarm_logic
    environment:
      - RABBITMQ_HOST='10.50.164.38'
      - PEER_SERVER_URL='10.50.174.37:8055'
      - WEIGHT_SERVER=100
      - SERVER_PORT=8055
      - PEER_NODE_NAME="sdc"
      - NODE_NAME="kr01"
      - ZBX_API_URL="http://10.50.164.38:8282/api_jsonrpc.php"
      - ZBX_API_TOKEN='c433fa5605593dd9bd3c1607de703ed7ac37a1542dec070ee94dbbdb7ff30f2a'
      - ALARM_HOST_NAME="EXTERNAL_SYSTEM_ALARM_MANAGER"
    networks:
      - app-network
    volumes:
      - /opt/rabbitmq_logs:/var/log/rabbitmq
    ports:
      - "8055:8055"

networks:
  app-network:
    driver: bridge
_________________

docker-compose build --no-cache
docker-compose up -d
docker ps

"""





from fastapi import FastAPI
import time
import uvicorn
from concurrent.futures import ThreadPoolExecutor

#sys.path.append('/opt/zabbix_custom/zabbix_AM/')

from my_env import initial_role, peer_server_url, weight_server, server_port, peer_node_name, node_name
from consumer import consumer_core

app = FastAPI()

def manage_consumer():
    while True:
        try:
            consumer_core()
            time.sleep(2)
        except Exception as e:
            print(f"Error in manage_consumer: {e}. Restarting function...")
            time.sleep(1)

def run_webserver():
    while True:
        try:
            uvicorn.run(app, host="0.0.0.0", port=server_port)
        except Exception as e:
            print(f"Error in run_webserver: {e}. Restarting function...")
            time.sleep(1)

def start_threads():
            executor = ThreadPoolExecutor(max_workers=2)
            executor.submit(run_webserver)
            executor.submit(manage_consumer)

if __name__ == "__main__":
            start_threads()

