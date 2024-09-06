



import subprocess
import threading
import time
import sys
import logging
import json
from pyzabbix import ZabbixAPI

#sys.path.append('/opt/zabbix_custom/zabbix_AM/')

from my_env import ZBX_SENDER_URL_KR01,ZBX_SENDER_URL_SDC,ZBX_API_URL,ZBX_API_TOKEN
from producer import rb_producer


zapi = ZabbixAPI(ZBX_API_URL)
zapi.login(api_token=ZBX_API_TOKEN)
zapi.session.verify = False


#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_trigger_problem(**kwargs):
    """Проверка, есть ли активная проблема по триггеру в данный момент."""
    try:
        trigger_id = kwargs.get("trigger_id", None)
        # Получение информации о триггере и проверка активных проблем
        triggers = zapi.trigger.get(
            triggerids=trigger_id,
            only_true=1,  # Получить только триггеры, находящиеся в состоянии проблемы
            output=['triggerid', 'description', 'priority', 'value'],
            selectLastEvent=['eventid', 'clock', 'name', 'acknowledged'],  # Получение последнего события по триггеру
            expandDescription=1  # Раскрыть макросы в описании
        )
        if not triggers:
            logging.info(f"No active problems found for trigger ID {trigger_id}")
            return False
        else:
            return True
    except Exception as e:
        logging.error(f"Failed to check trigger problem: {e}")
        return False


def run_zabbix_sender(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    if stdout:
        print(f"stdout: {stdout}")
    if stderr:
        print(f"stderr: {stderr}")

def prepare_data_to_zabbix(message):
    sender_check = False
    hostname = message.get('host_name', None)
    key = message.get('key', None)
    value = message.get('value', None)
    short_alarm = message.get('short_alarm', "False")
    trigger_id = message.get('trigger_id', None)
    time.sleep(10)
    while sender_check == False:
        if hostname and key and value:
            command = [
                "zabbix_sender",
                "-z", ZBX_SENDER_URL_KR01,
                "-p", "10051",
                "-s", hostname,
                "-k", key,
                "-o", str(value)
            ]
            run_zabbix_sender(command)
            command = [
                "zabbix_sender",
                "-z", ZBX_SENDER_URL_SDC,
                "-p", "10051",
                "-s", hostname,
                "-k", key,
                "-o", str(value)
            ]
            run_zabbix_sender(command)
            time.sleep(1)
            sender_check = check_trigger_problem(**message)
            if sender_check == True:
                if str(short_alarm) == "True" and str(trigger_id) != None:
                    # logging.info(f"\n\nHERE IS TEST! \n\n")
                    message_json = json.dumps(message)
                    bytes_message = message_json.encode('utf-8')
                    rb_producer(bytes_message)
                    logging.info(f"message sent in RabbitMQ: {message}")
                    return [True, hostname]
                return [True, hostname]
            else:
                continue
        else:
            return [False,hostname]

#my_message = {'host_name': 'EXTERNAL_SYSTEM_ALARM_MANAGER', 'key': 'external.alert[000000000000000000000001.Event Definition Test Title]', 'value': 1, 'short_alarm': 'True', 'trigger_id': '206489'}

#run_zabbix_sender(my_message)
