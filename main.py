from request import Request
from queue import Queue

def main():
    requester = Request()

    requester.start()
    requester.join()

if __name__ == '__main__':
    main()
