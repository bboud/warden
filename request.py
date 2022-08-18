from threading import Thread
from gpiozero import PWMLED, Button, GPIOPinInUse, LED
from time import sleep
from led_controller import LEDController
from queue import Queue
import requests

WARNING_TYPES = {
    'Flash Flood Warning',
    'Severe Thunderstorm Warning',
    'Tornado Warning',
    'Special Weather Statement'
        }

class Request(Thread):
    def __init__(self):
        super().__init__()

        self.graveyard = {}

        self.error_led = LED(16)

        self.lcq = Queue()
        self.led_controller = LEDController(self.lcq).start()

    def run(self):
        STATE_CODE = "AZ"

        while True:
            try:
                req = requests.get(f'https://api.weather.gov/alerts/active?area={STATE_CODE}')
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

            buffer_ids = {}

            # Pass all the new features along:
            for feature in buffer['features']:
                event = feature['properties']['event']
                message = feature['properties']['messageType']

                if not event in WARNING_TYPES: continue
                
                buffer_ids[feature['id']] = feature

                if feature['id'] in self.graveyard: continue

                self.graveyard[feature['id']] = feature

                print(message)

                # Need to add for update alerts on startup
                if message == 'Alert' or message == 'Update':
                    print(f'Signal to push {event}')
                    self.lcq.put( ('push', event) )

            who_to_delete = []

            for k, v in self.graveyard.items():
                if k not in buffer_ids:
                    print(f'Expiring {k}')
                    self.lcq.put( ( 'pop', v['properties']['event'] ) )
                    who_to_delete.append(k)
                    print(self.graveyard)
            for item in who_to_delete:
                del self.graveyard[item]

            sleep(10)
