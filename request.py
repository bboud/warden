from threading import Thread
from gpiozero import PWMLED, Button, GPIOPinInUse, LED
from requests import get, Timeout
from time import sleep
from collections import deque
import requests
import queue

WARNING_TYPES = {
    'Flash Flood Warning',
    'Severe Thunderstorm Warning',
    'Tornado Warning',
    'Special Weather Statement'
        }

class Request(Thread):
    def __init__(self, alert_controller_queue):
        super().__init__()

        self.id_graveyard = []
        self.threads = []

        self.acq = alert_controller_queue

        self.error_led = LED(16)

    def run(self):
        STATE_CODE = "TX"

        while True:
            try:
                req = get(f'https://api.weather.gov/alerts/active?area={STATE_CODE}')
            except requests.Timeout as e:
                print(e)
                print('API is timing out! Sleeping for 30 seconds.')
                self.error_led.blink(n=15)
                sleep(30)
                continue
            except requests.ConnectionError as e:
                print(e)
                print('Network connection error. Please check network connection. Sleeping for 30 seconds.')
                self.error_led.blink(n=15)
                sleep(30)
                continue

            if req.status_code != 200:
                print(f'Request failed with status code {req.status_code}')
                # Exit as API call is not valid and will never work.
                break

            buffer = req.json()

            if not buffer['features']:
                print('No alerts.')
                sleep(10)
                continue

            for feature in buffer['features']:
                if feature['id'] in self.id_graveyard: continue

                event = feature['properties']['event']

                if not event in WARNING_TYPES: continue

                self.id_graveyard.append(feature['id'])

                self.acq.put(('alert', feature))

            sleep(10)
        for t in self.threads:
            t.join()
