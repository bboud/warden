from threading import Thread
from gpiozero import PWMLED, Button, GPIOPinInUse, LED
from requests import get, Timeout
from time import sleep
from collections import deque
import requests
import queue

WARNING_TYPES = {
    'Flash Flood Warning'
        }

class Ack(Thread):
    def __init__(self, ackq):
        super().__init__()
        self.ack_led = PWMLED(21)
        self.ack_button = Button(20)
        self.ackq = ackq

    def run(self):
        self.ack_led.pulse()
        self.ack_button.wait_for_press()
        self.ack_led.off()

        #Closing too close to the off call might cause segfaulting
        sleep(1)

        # Make sure these are no longer in use
        self.ack_led.close()
        self.ack_button.close()
        
        # Return to default state
        self.ackq.put(False)

class Request(Thread):
    def __init__(self, alert_controller_queue):
        super().__init__()

        self.acq = alert_controller_queue
        self.ackq = queue.Queue()
        self.acked = False

        self.id_graveyard = []
        self.threads = []

        self.error_led = LED(16)

    def run(self):
        STATE_CODE = "AZ"

        while True:
            try:
                self.acked = self.ackq.get_nowait()
            except queue.Empty:
                pass

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

                print(event)

                self.acq.put(feature)

                try:
                    if not self.acked:
                        self.acked = True
                        self.threads.append(Ack(self.ackq).start())
                except RuntimeError as e:
                    print(e)
                    continue
            sleep(10)
        for t in self.threads:
            t.join()
