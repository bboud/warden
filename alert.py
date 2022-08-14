from threading import Thread
from gpiozero import PWMLED
from time import sleep
import queue

class AlertController(Thread):
    def __init__(self, acq):
        super().__init__()
        self.acq = acq

        self.flood_led = PWMLED(27)
        self.thunder_led = PWMLED(17)
        self.tornado_led = PWMLED(22)
        self.sws_led = PWMLED(18)

        self.alert_queue = {}

    def update_led(self, string, event, messageType, led):
        if string in event:
            if 'Warning' in event:
                if messageType == 'Update' or messageType == 'Alert': led.blink(on_time=0.2, off_time=0.2)
                sleep(2)
                led.on()

                if messageType == 'Cancel': led.off()
            elif 'Watch' in event:
                led.blink(on_time=1, off_time=5)
            elif 'Special' in event:
                if messageType == 'Update' or messageType == 'Alert': led.blink(on_time=0.2, off_time=0.2)
                sleep(2)
                led.pulse()

                if messageType == 'Cancel': led.off()


    def run(self):
        while True:
            alert = self.acq.get()
            aid = alert['id']
            props = alert['properties']
            messageType = props['messageType']
            event = props['event']

            self.update_led('Flood', event, messageType, self.flood_led)
            self.update_led('Thunder', event, messageType, self.thunder_led)
            self.update_led('Tornado', event, messageType, self.tornado_led)
            self.update_led('Special', event, messageType, self.sws_led)
