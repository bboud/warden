import gpiozero as pi
import threading

from time import sleep

import requests

ack_led = pi.PWMLED(17)
button = pi.Button(4)

def ack():
	ack_led.pulse()

	button.wait_for_press()

	ack_led.off()

def main():
    # The state to activate the warden for
    STATE_CODE = "CA"

    # Features we have already seen and alerted
    recognized_features = {}

    ack_thread = threading.Thread(target=ack)

    while True:
        req = requests.get("https://api.weather.gov/alerts/active?area=" + STATE_CODE)
        status = req.status_code
        if status != 200:
            print("Error: Status code: " + str(status))
            continue
        buffer = req.json()
        if not buffer["features"]:
            print("There are no alerts at this time :)")
            sleep(10)
            continue

        # If there are no elements if the recognized features, funnel the population of the requests here:
        # This should only run on the first run of this loop OR if for some reason the API is timing out and isn't
        # able to update. We want to populate the list prior to pinging discord so that all the alerts aren't being
        # posted to discord at once.
        if len(recognized_features) < 1:
            for feature in buffer["features"]:
                if (feature["id"] not in recognized_features):
                    print("New feature detected: " + feature["id"])
                    recognized_features[feature["id"]] = feature["properties"]
                    try:
                        ack_thread.start()
                    except RuntimeError:
                        if not ack_thread.is_alive():
                            ack_thread.join()
                            ack_thread = threading.Thread(target=ack)
                            ack_thread.start()
                        print("Already awaiting ack..")
                        print(ack_thread.is_alive())
                else:
                    continue
            continue

        for feature in buffer["features"]:
            if (feature["id"] not in recognized_features):
                print("New feature detected: " + feature["id"])
                recognized_features[feature["id"]] = feature["properties"]
                try:
                     ack_thread.start()
                except RuntimeError:
                    if not ack_thread.is_alive():
                        ack_thread.join()
                        ack_thread = threading.Thread(target=ack)
                        ack_thread.start()
                    print("Already awaiting ack..")
                    print(ack_thread.is_alive())
            else:
                continue

if __name__ == '__main__':
    main()
