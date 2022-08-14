from threading import Thread
from gpiozero import PWMLED, Button
from requests import get

class Ack(Thread):
    def __init__(self):
        super().__init__()
        self.ack_led = PWMLED(21)
        self.ack_button = Button(20)

    def run(self):
        self.ack_led.pulse()
        self.ack_button.wait_for_press()
        self.ack_led.off()

class Request(Thread):
    def __init__(self, same_info=[], location_info=[]):
        super().__init__()
        self.ack = Ack()
        self.alert_threads = []

        self.id_graveyard = []

    def run(self):
        STATE_CODE = "AZ"

        while True:
            req = get(f'https://api.weather.gov/alerts/active?area={STATE_CODE}')
            if req.status_code != 200:
                print(f'Request failed with status code {req.status_code}')
                continue

            buffer = req.json()

            if not buffer['features']:
                sleep(10)
                continue

            for feature in buffer['features']:
                if feature['id'] in self.id_graveyard: continue
                print(feature['id'])
                self.id_graveyard.append(feature['id'])
                try:
                    self.ack.start()
                except RuntimeError:
                    if not self.ack.is_alive():
                        self.ack.join()
                        self.ack = Ack()
                        self.ack.start()
        sleep(10)

