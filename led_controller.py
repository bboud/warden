from threading import Thread
from gpiozero import PWMLED, Button
from time import sleep
import gpiozero

ACK_PIN = 20
 
def listen_for_ack(lcq, event):
    try:
        button = Button(ACK_PIN)
    except gpiozero.GPIOPinInUse:
        return
 
    button.wait_for_press()

    lcq.put(('ack', event))
 
    sleep(1)
 
    button.close()

class LEDController(Thread):
    def __init__(self, led_controller_queue):
        super().__init__()

        self.lcq = led_controller_queue

        self.ack_thread = None
        self.acked = True

        # Count, LED, Acked
        self.led_map = {
            'Flash Flood Warning': [0, PWMLED(27), True],
            'Severe Thunderstorm Warning': [0, PWMLED(17), True],
            'Tornado Warning': [0, PWMLED(22), True],
            'Special Weather Statement': [0, PWMLED(18), True]
                }

    def run(self):
        while True:
            update = self.lcq.get()
            print(f'Recieved {update[0]}')
            if update[0] == 'ack':
                self.ack_thread = None
                for led in self.led_map.values():
                    led[2] = True

            elif update[0] == 'push':
                print('Pushing element')
                event = update[1]

                # Ack starting control depends on the pin being bound.
                self.ack_thread = Thread(target=listen_for_ack, args=(self.lcq, event,)).start()

                self.led_map[event][2] = False
                self.led_map[event][0] += 1
                print(self.led_map[event][0])

            elif update[0] == 'pop':
                print('Popping element')
                event = update[1]
                count = self.led_map[event][0]

                if count <= 0: continue
                self.led_map[event][0] -= 1
                print(self.led_map[event][0])

            for led in self.led_map.values():
                count = led[0]
                led_obj = led[1]
                acked = led[2]

                if not acked:
                    led_obj.blink(on_time=0.2, off_time=0.2)
                else:
                    if count > 0:
                        led_obj.on()
                    else:
                        led_obj.off()
