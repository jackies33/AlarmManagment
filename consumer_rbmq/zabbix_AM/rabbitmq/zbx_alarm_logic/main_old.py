

'''
for daemon setup script
create  - >> "mcedit /etc/systemd/system/zbx_alarm_proxy.service"
copy in zbx_alarm_proxy.service ->>
_______________________________

[Unit]
Description=Listen and classifier web hooks from netbox App through RabbitMQ

[Service]
ExecStart=/usr/bin/python3 /opt/zabbix_custom/zabbix_AM/rabbitmq/main.py
StandardOutput=file:/var/log/rabbitmq/output_sys.log
StandardError=file:/var/log/rabbitmq/error.log
Restart=always

[Install]
WantedBy=multi-user.target
_________________________________

<<----copy in zbx_alarm_proxy.service

run next commands -->>>
_____________________________
sudo systemctl daemon-reload
sudo systemctl enable zbx_alarm_proxy.service
sudo systemctl start zbx_alarm_proxy.service

______________________________

<<--- run next commands

###for use command and check service status do next

>>mcedit ~/zbx_alarm_proxy
copy there :

#!/bin/bash
python3 /opt/zabbix_custom/zabbix_AM/rabbitmq/main.py "$@"


>>chmod +x ~/zbx_alarm_proxy

>>sudo mv ~/zbx_alarm_proxy /usr/local/bin/

use next command:   -   zbx_alarm_proxy --status



'''




from fastapi import FastAPI, Response
import time
import uvicorn
import threading
import requests
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor

sys.path.append('/opt/zabbix_custom/zabbix_AM/')

from rabbitmq.my_env import initial_role, peer_server_url, weight_server, server_port,peer_node_name,node_name
from rabbitmq.consumer import consumer_core

app = FastAPI()
initial_role = initial_role
last_heartbeat_time = time.time()
times_check = 2

role_lock = threading.Lock()


@app.post("/heartbeat")
def heartbeat():
    global last_heartbeat_time
    last_heartbeat_time = time.time()
    return Response(status_code=200)

@app.get("/status")
def status():
    with role_lock:
        current_role = initial_role
    return {"status": current_role}

def send_heartbeat():
    global initial_role, times_check
    while True:
        with role_lock:
            current_role = initial_role
            check_count = times_check
        if current_role == 'standby' and check_count > 0:
            try:
                response = requests.post(f'http://{peer_server_url}/heartbeat')
                if response.status_code != 200:
                    with role_lock:
                        times_check -= 1
            except requests.exceptions.RequestException:
                with role_lock:
                    times_check -= 1
        elif current_role == 'standby' and check_count <= 0:
            with role_lock:
                initial_role = 'active'
                times_check = 2
        elif current_role == 'active':
            try:
                response = requests.post(f'http://{peer_server_url}/heartbeat')
                if response.status_code != 200:
                    print("Failed to send heartbeat to peer server.")
                elif response.status_code == 200 and weight_server == 50:
                    with role_lock:
                        initial_role = 'standby'
                        times_check = 2
                elif response.status_code == 200 and weight_server == 100:
                    pass
            except requests.exceptions.RequestException:
               print("Peer server is down or unreachable.")
        time.sleep(5)

def manage_consumer():
    global initial_role
    while True:
        with role_lock:
            current_role = initial_role
        if current_role == 'active':
            consumer_core()
        time.sleep(0.1)

def run_webserver():
    uvicorn.run(app, host="0.0.0.0", port=server_port)

def start_threads():
    executor = ThreadPoolExecutor(max_workers=3)
    executor.submit(run_webserver)
    executor.submit(send_heartbeat)
    executor.submit(manage_consumer)

def check_status():
    try:
        local_status = requests.get(f'http://127.0.0.1:{server_port}/status').json()['status']
    except requests.exceptions.RequestException:
        local_status = "unreachable"

    try:
        peer_status = requests.get(f'http://{peer_server_url}/status').json()['status']
    except requests.exceptions.RequestException:
        peer_status = "unreachable"

    print(f"{node_name}==[{local_status}]==")
    print(f"{peer_node_name}==[{peer_status}]==")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Consumer HA')
    parser.add_argument('--status', action='store_true', help='Check the status of both instances')

    args = parser.parse_args()

    if args.status:
        check_status()
    else:
        start_threads()


