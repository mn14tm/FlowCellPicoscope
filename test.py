from serial import *
from threading import Thread
from queue import Queue


def receiving(ser, q):
    # Wait for arduino buffer to fill up
    time.sleep(3)

    last_received = 'None'
    buffer_string = ''
    a = 0
    while True:
        buffer_string += ser.read(ser.inWaiting()).decode('utf-8')
        if '\n' in buffer_string:
            lines = buffer_string.split('\n')  # Guaranteed to have at least 2 entries
            last_received = lines[-2]
            time.sleep(0.5)  # queue needs this for some reason
            q.put(last_received)


def thread(q):
    time.sleep(3)
    while True:
        last_received = q.get()
        print(last_received)
        time.sleep(1)


if __name__ == '__main__':

    arduino = Serial(
        port='/dev/tty.usbmodem621',
        baudrate=9600,
        timeout=1
    )

    queue = Queue()
    thread1 = Thread(target=receiving, args=(arduino, queue))
    thread2 = Thread(target=thread, args=(queue,))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    print("Hi")
