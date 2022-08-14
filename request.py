from threading import Thread
from gpiozero import PWMLED, Button, GPIOPinInUse
from requests import get, Timeout
from time import sleep
import requests

class Ack(Thread):
    def __init__(self):
        super().__init__()
        self.ack_led = PWMLED(21)
        self.ack_button = Button(20)

    def run(self):
        try:
            self.ack_led.pulse()
            self.ack_button.wait_for_press()
            self.ack_led.off()
        except GPIOPinInUse:
            print('GPIO ACK Pin in use!')

        # Must delete or else pins will stay in use!
        del self.ack_led
        del self.ack_button

class Request(Thread):
    def __init__(self, same_info=[], location_info=[]):
        super().__init__()
        self.ack = Ack()

        # Key: ID, Value: Alert Thread
        self.alerts = {}

        self.id_graveyard = []

    def run(self):
        STATE_CODE = "AZ"

        while True:
            try:
                req = get(f'https://api.weather.gov/alerts/active?area={STATE_CODE}')
            except requests.Timeout:
                print('API is timing out! Sleeping for 30 seconds.')
                sleep(30)
                continue
            except requests.ConnectionError:
                print('Network connection error. Please check network connection. Sleeping for 30 seconds.')
                sleep(30)
                continue

            if req.status_code != 200:
                print(f'Request failed with status code {req.status_code}')
                # Exit as API call is not valid and will never work.
                exit()

            buffer = req.json()

            if not buffer['features']:
                print('No alerts.')
                sleep(10)
                continue

            for feature in buffer['features']:
                if feature['id'] in self.id_graveyard: continue

                print(feature['id'])

                properties = feature['properties']

                print(properties['event'])

                self.id_graveyard.append(feature['id'])

                try:
                    self.ack.start()
                except RuntimeError:
                    # If the current ack thread is dead, start a new one.
                    if not self.ack.is_alive():
                        self.ack = Ack()
                        self.ack.start()
                    sleep(10)
                    continue
