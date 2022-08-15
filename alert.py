from threading import Thread
from gpiozero import PWMLED, Button
from time import sleep
from queue import Queue
from datetime import datetime
import requests
import threading
import gpiozero

LED_PINS = {
    'Flash Flood Warning': 27,
    'Severe Thunderstorm Warning': 17,
    'Tornado Warning': 22,
    'Special Weather Statement': 18
        }

ACK_PIN = 20

def listen_for_ack(acq):
    try:
        button = Button(ACK_PIN)
    except gpiozero.GPIOPinInUse:
        return

    button.wait_for_press()

    acq.put(('ack',))

    sleep(1)

    button.close()


class Alert(Thread):
    def __init__(self, feature, update_queue):
        super().__init__()
        self.id = feature['id']
        self.properties = feature['properties']
        self.expires = datetime.fromisoformat(self.properties['expires'])
        self.event = self.properties['event']
        
        try:
            self.led = PWMLED( LED_PINS[self.event] )
        except:
            self.led = None

        self.acked = False

        self.update_queue = update_queue

        print(f'{self.event} is now active')

    def try_led_update(self):
        if not self.led:
            return

        try:
            if self.acked:
                self.led.on()
            else:
                self.led.blink(on_time=0.2, off_time=0.2)
        except gpiozero.GPIOPinInUse:
            pass

    def expire(self):
        try:
            self.led.off()
        except gpiozero.GPIOPinInUse:
            pass

    def run(self):
        self.try_led_update()
        while True:
            # Handle Expiration And Update
            try:
                print(f'{self.event} is now waiting')
                update = self.update_queue.get()
                if update[0] == 'ack':
                    self.acked = True
                    self.try_led_update()
            except:
                pass


class AlertController(Thread):
    def __init__(self, acq):
        super().__init__()
        self.acq = acq

        self.alerts = {}

        self.ack_threads = []
        self.alert_threads = []

    def run(self):
        while True:
            acq_value = self.acq.get()

            if acq_value[0] == 'ack':
                for alert in self.alerts.values():
                    alert.put(('ack',))
                for thread in self.ack_threads:
                    thread.join()
            elif acq_value[0] == 'alert':
                alert = acq_value[1]
                update_queue = Queue()

                self.alerts[alert['id']] = update_queue
                self.alert_threads.append( Alert( alert, update_queue ).start() )

                ack_thread = threading.Thread(target=listen_for_ack, args=(self.acq, ))
                self.ack_threads.append(ack_thread)
                ack_thread.start()

        for thread in self.ack_threads:
            thread.join()
        for thread in self.alert_threads:
            thread.join()
