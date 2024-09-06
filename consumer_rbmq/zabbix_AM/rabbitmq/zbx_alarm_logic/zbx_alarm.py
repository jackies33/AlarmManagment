


from pyzabbix import ZabbixAPI
import sys
import logging
import json
import time

#sys.path.append('/opt/zabbix_custom/zabbix_AM/')

from my_env import ZBX_API_URL, ZBX_API_TOKEN, ALARM_HOST_NAME, ZBX_SHORT_ALARMS_LIST
from producer import rb_producer
from grlg_get import GRLG_GET


zapi = ZabbixAPI(ZBX_API_URL)
zapi.login(api_token=ZBX_API_TOKEN)
zapi.session.verify = False


def alert_logic(queue_name, alert):
    try:
        event_alert_true = alert.get('event_alert','true')
        if event_alert_true == "true":                          ####find all fields for find or create item in zabbix
            alert_source = alert.get('event_source', queue_name)
            alarm_host = zapi.host.get(filter={"host": ALARM_HOST_NAME})[0]
            host_id = alarm_host["hostid"]
            alert_event_name = alert.get('event_name', "Undefined_event")
            item_key = f"external.alert[{alert_source}.{alert_event_name}]"
            items = zapi.item.get(filter={"hostid": host_id, "key_": item_key})
            alert_description = alert.get('event_description', None)
            alarm_id = alert.get("event_id", None)
            link_for_event = alert.get("link", "link")
            if not items:
                try:
                    zapi.item.create(
                        hostid=host_id,
                        name=f"Alert from {alert_source} - {alert_event_name}",
                        key_=item_key,
                        type=2,
                        value_type=3,
                        description=alert_description,
                    )
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            alert_severity = int(alert.get('event_severity', 4))  ####find all fields and tags for find or create trigger in zabbix
            #alert_message = alert.get('event_message',
            #                          f"Message from external system -  {alert_source}, got with empty message field. "
            #                          f"Please check details of alarm directly in event source")
            alert_backlog = alert.get('backlog', {}).get('last_messages', [])
            alarm_key = alert.get("event_key", None)
            tags = []
            tags.append({"tag":"source_for_define","value":alert_source})
            tags.append({"tag":"event_id", "value":alarm_id})
            tags.append({"tag":"link_fort_event", "value":link_for_event})
            tags.append({"tag":"alert_event_name", "value":alert_event_name})
            for message in alert_backlog:
                for key, value in message.items():
                    tags.append({'tag': key, 'value': value})
            if alarm_id == "134":
                time.sleep(5)#wait for apeers a data in graylog events
                call = GRLG_GET()
                get_grlg_data = call.grlg_get_event_info(**{"event_id":alarm_key})
                if get_grlg_data[0] == True:
                    #tags.append({"tag":"user_name", "value":get_grlg_data[1]["user_name"]})
                    #tags.append({"tag": "ip_source", "value": get_grlg_data[1]["ip_source"]})
                    tags.append({"tag": "count", "value": get_grlg_data[1]["count_efforts"]})
            event_name_for_zabbix = f"{alert_event_name} ###event_key_{alarm_key}###"
            triggers = zapi.trigger.get(filter={"event_name": event_name_for_zabbix})
            trigger_id = None
            if triggers:
                trigger_id = triggers[0]['triggerid']
            elif not triggers:
                try:
                    result = zapi.trigger.create(
                        description=alert_description,
                        expression=f"last(/{ALARM_HOST_NAME}/{item_key})=1",
                        priority=alert_severity,
                        comments=f'{alert_description}',
                        event_name=event_name_for_zabbix,
                        tags=tags
                    )
                    trigger_id = result.get('triggerids', [])[0]
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            short_alarm = "False"
            if alert.get("event_interruption", "False") == "True": # if "event_interruption" == "True" , close alarm after escalation
                short_alarm = "True"
            #for al in ZBX_SHORT_ALARMS_LIST: # if id the same like in list , close alarm after escalation
            #    if str(al) == str(alarm_id):
            #        short_alarm = "True"
            json_message = json.dumps({"host_name": ALARM_HOST_NAME, "key": item_key, "value": 1,
                                       "short_alarm": short_alarm, "trigger_id": trigger_id})
            bytes_message = json_message.encode('utf-8')
            rb_producer(bytes_message)
            #for i in range(5):
             #   thread = delayed_send_data_to_zabbix({"host_name":ALARM_HOST_NAME, "key":item_key,"value": 1})
              #  thread.join()
                #delayed_send_data_to_zabbix(ALARM_HOST_NAME, item_key, 1)
            return {"status": "success"}
    except Exception as err:
        return {"status": "failed", "error": str(err)}






my_alarm = {'event_name': 'Подозрительная активность',
            'event_description': 'Успешное подключение к ВПН клиента, находящегося за пределами Российской Федерации',
            'event_type': 'aggregation-v1',
            'event_id': '133',
            'event_timestamp': '2024-08-06T05:10:25.430+03:00',
            'event_source': 'sdc-net-log-graylog01',
            'event_key': '',
            'event_priority': '3',
            'event_alert': 'true',
            'event_timestamp_processing': '2024-08-06T05:10:25.430+03:00',
            'backlog': {'last_messages': [{'vpn': 'vpn-gw01',
                                           'time': 'Aug 06 2024 05:10:25',
                                           'user': 'MorozovAnVl',
                                           'source_ip': '212.175.95.12',
                                           'country': 'Турция',
                                           'city': 'Анкара',
                                           'link': 'https://grlg.net.tech.mosreg.ru/messages/cisco_asa_syslog_35/0b2bdb60-5399-11ef-846a-005056abc809'}]}}