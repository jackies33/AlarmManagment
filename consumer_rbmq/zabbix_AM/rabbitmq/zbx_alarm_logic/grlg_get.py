


import requests
from requests.auth import HTTPBasicAuth
import re

from my_env import GRAYLOG_URL,GRLG_LOGIN,GLRG_PASSWORD



class GRLG_GET():

    def __init__(self):

        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def grlg_get_event_info(self,**kwargs):
        event_id = kwargs["event_id"]
        try:
            response = requests.get(f"{GRAYLOG_URL}/events/{event_id}",auth=HTTPBasicAuth(GRLG_LOGIN, GLRG_PASSWORD),
                                    verify=False, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            event = data['event']
            #groups_by_fileds = event['group_by_fields']
            message = event['message']
            #user_name_and_ip = re.findall(r"\S+\|\S+", message)[0]
            #user_name = user_name_and_ip.split("|")[0]
            #ip_source = user_name_and_ip.split("|")[1]
            count_efforts = re.findall(r"count\(\S+\)=\d+", message)[0].split("=")[1]
            #return [True,{"event":event,"user_name":user_name, "ip_source":ip_source,"count_efforts":count_efforts}]
            return [True,{"count_efforts":count_efforts}]
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve data: {e}")
            return [False,None]
        except Exception as e:
            print(f"Failed to retrieve data: {e}")
            return [False,None]








