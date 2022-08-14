from request import Request
from queue import Queue
from alert import AlertController

def main():
    alert_controller_queue = Queue()
    requester = Request(alert_controller_queue)
    ac = AlertController(alert_controller_queue)

    requester.start()
    ac.start()

    requester.join()
    ac.join()

if __name__ == '__main__':
    main()
