

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
        trigger_id = message.get('trigger_id', None)
        zapi.trigger.delete(trigger_id)
        print(err)





"""
def zbx_deleter_trigger_with_delay(message):
    # Декодирование сообщения, если оно в формате bytes
    if isinstance(message, bytes):
        try:
            message = message.decode('utf-8')
            message = json.loads(message)
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            print(f"Error decoding or parsing JSON: {err}")
            return

    # Извлечение trigger_id
    trigger_id = message.get('trigger_id', None)
    if not trigger_id:
        print("No trigger_id found in the message.")
        return

    count_for_atempts = 10
    # Удаление триггера с проверкой его наличия
    while count_for_atempts < 1:
        try:
            count_for_atempts = count_for_atempts - 1
            # Проверка существования триггера
            trigger = zapi.trigger.get(triggerids=trigger_id)
            if not trigger:
                print(f"Trigger {trigger_id} successfully deleted.")
            else:
                # Удаление триггера
                zapi.trigger.delete(trigger_id)
                print(f"Trigger {trigger_id} deleted. Rechecking...")
                time.sleep(5)  # Задержка перед повторной проверкой
        except Exception as err:
            print(f"Error while deleting trigger {trigger_id}: {err}")
            time.sleep(5)  # Задержка перед повторной попыткой
"""
