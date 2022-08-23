#!/usr/bin/env python3

from pathlib import Path
from signal import pause
import mraa
import toml
from pythonosc import udp_client
from debugs import debug

DEBUG = None
IP = None
OUT_PORT = None
BUTTONS = None
BUTTONS_DATA = None
CLIENT = None
MAINPATH = Path(__file__).parent.absolute()
CONFIG_PATH = MAINPATH / Path('rot_config.toml')
PRESSED = 0
RELEASED = 1


def init_config():
    global IP, OUT_PORT, BUTTONS, DEBUG

    with open(CONFIG_PATH, 'r') as f:
        data = toml.load(f)

    DEBUG = data['debug']['DEBUG']
    IP = data['network']['IP']
    OUT_PORT = data['network']['OUT_PORT']
    BUTTONS = [data['buttons'][but] for but in data['buttons']]
    CLIENT = udp_client.SimpleUDPClient(IP, OUT_PORT)


def button_isr_routine(gpio):
    if gpio.read() == PRESSED:
        debug(DEBUG, "PRESSED")
    else:
        debug(DEBUG, "RELEASED")
    print(dir(gpio))


def button_config(pin):
    button = mraa.Gpio(pin)
    button.dir(mraa.DIR_IN)
    # button.mode(mraa.MODE_PULLUP)
    button.isr(mraa.EDGE_BOTH, button_isr_routine, button)
    return button


class But:
    PRESSED = 0
    RELEASED = 1

    def __init__(self, pin, address):
        self.button = mraa.Gpio(pin)
        self.button.dir(mraa.DIR_IN)
        self.address = address
        self.last = RELEASED

    def update(self, sender_func):
        value = self.button.read()
        if value != self.last:
            self.last = value
            debug(DEBUG, f"{self.address}: {1 - value}")
            sender_func(self.address, 1 - value)
            return value
        else:
            return None


if __name__ == '__main__':
    init_config()
    client = udp_client.SimpleUDPClient(IP, OUT_PORT)

    buttons = [But(but['PIN'], but['ADDRESS']) for but in BUTTONS]

    while True:
        list(map(lambda x: x.update(client.send_message), buttons))
