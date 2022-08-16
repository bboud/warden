from threading import Thread
from queue import Queue
from datetime import datetime
from led_controller import LEDController
from time import sleep
import requests
import time

class Alert(Thread):
    def __init__(self, feature, update_queue, acq):
        super().__init__()
        self.feature = feature
        self.id = feature['id']
        self.effective = datetime.timestamp(datetime.fromisoformat(feature['properties']['effective']))
        self.expires = datetime.timestamp(datetime.fromisoformat(feature['properties']['expires']))
        self.event = feature['properties']['event']

        diff = self.expires - self.effective
        self.expire_time = time.time() + diff

        self.update_queue = update_queue
        self.acq = acq

    def run(self):
        while True:
            try:
                message = self.update_queue.get_nowait()
                if message[0] == 'update':
                    self.expires = datetime.timestamp(datetime.fromisoformat(message[1]))
                    diff = self.expires - self.effective
                    self.expire_time = time.time() + diff
            except:
                pass

            if self.expire_time <= time.time():
                self.feature['properties']['messageType'] = 'Expire'
                self.acq.put(self.feature)
                break

            sleep(10)

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
            alert = self.acq.get()
            print(alert['properties']['messageType'])
            print(alert['id'])
            
            if alert['properties']['messageType'] == 'Alert':
                if alert['id'] in self.alerts: continue
                self.lcq.put( ('push', alert['properties']['event']) )

                update_queue = Queue()

                self.alerts[alert['id']] = update_queue
                self.alert_threads[alert['id']] = Alert( alert, update_queue, self.acq ).start()

            elif alert['properties']['messageType'] == 'Update':
                references = alert['properties']['references']

                for ref in references:
                    print(ref['@id'])
                    if ref['@id'] in self.alerts.values():
                        print(f'Updating {alert["id"]}')
                        self.alerts[ref].put( ('update', alert['properties']['expires']) )
                    else:
                        #This might create duplicates - investigate this later
                        altered_alert = alert
                        altered_alert['properties']['messageType'] = 'Alert'
                        self.acq.put( altered_alert )
            elif (alert['properties']['messageType'] == 'Expire' or alert['properties']['messageType'] == 'Cancel') and ( alert['id'] in self.alerts ):
                print('Expiring!')
                self.lcq.put( ('pop', alert['properties']['event']) )
                del self.alerts[alert['id']] 


        for thread in self.alert_threads.values():
            thread.join()
