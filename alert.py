from threading import Thread
from gpiozero import PWMLED, Button
from queue import Queue
from datetime import datetime
from led_controller import LEDController
import requests

class Alert(Thread):
    def __init__(self, feature, update_queue):
        super().__init__()
        self.id = feature['id']
        self.expires = datetime.fromisoformat(feature['properties']['expires'])
        self.event = feature['properties']['event']

        self.update_queue = update_queue

    def run(self):
          return

class AlertController(Thread):
    def __init__(self, acq):
        super().__init__()
        self.acq = acq

        self.alerts = {}
        self.alert_threads = {}

        self.lcq = Queue()
        self.led_controller = LEDController(self.lcq).start()

    def run(self):
        while True:
            acq_value = self.acq.get()
            alert = acq_value[1]

            print(f'putting {alert["id"]}')
            self.lcq.put( ('push', alert['properties']['event']) )

            if acq_value[0] == 'alert':
                alert = acq_value[1]
                update_queue = Queue()

                self.alerts[alert['id']] = update_queue
                self.alert_threads[alert['id']] = Alert( alert, update_queue ).start()

        for thread in self.alert_threads.values():
            thread.join()
