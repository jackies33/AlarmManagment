

from pyzabbix import ZabbixAPI
import time
import json

from my_env import ZBX_API_URL, ZBX_API_TOKEN


zapi = ZabbixAPI(ZBX_API_URL)
zapi.login(api_token=ZBX_API_TOKEN)
zapi.session.verify = False


def zbx_deleter_trigger_with_delay(message):
    if isinstance(message, bytes):
        try:
            message = message.decode('utf-8')
            message = json.loads(message)
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            print(f"Error Decoding or parsing JSON: {err}")
            return
    time.sleep(10)
    try:
        trigger_id = message.get('trigger_id', None)
        zapi.trigger.delete(trigger_id)
    except Exception as err:
        print(err)

