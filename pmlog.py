#!/usr/bin/python
import sys
import os
import time
import struct
import logging
import argparse
from collections import namedtuple
from threading import Event

from periphery import GPIO, Serial


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format='%(asctime)-15s %(levelname)-8s %(message)s')
log = logging.getLogger()


parser = argparse.ArgumentParser(description='PMS5003 data logger')
parser.add_argument(
        "-p", "--port", type=str, default="/dev/ttyS1",
        help="Serial port connected to the PMS5003 sensor")
parser.add_argument(
        "--reset-pin", type=int, default=None,
        help="GPIO number connected to the RESET signal")
parser.add_argument(
        "--enable-pin", type=int, default=None,
        help="GPIO number connected to the SET (enable) signal")


Packet = namedtuple('Packet', [
        'pm1_std', 'pm25_std', 'pm10_std', 'pm01_atm', 'pm25_atm',
        'concentration_unit', 'count_03um', 'count_05um', 'count_1um',
        'count_2_5um', 'count_5um', 'count_10um'])


class PMS5003(object):
    def __init__(self, port, enable_pin=None, reset_pin=None):
        self.port = Serial(port, 9600)
        self.gpio_enable = None
        self.gpio_reset = None
        self.stop = Event()

        # suspend sensor by default
        if enable_pin:
            self.gpio_enable = GPIO(enable_pin, "low")

        if reset_pin:
            self.gpio_reset = GPIO(reset_pin, "high")

    def reset(self):
        if self.gpio_reset is None:
            return

        self.gpio_reset.write(False)
        self.enable()
        time.sleep(.1)
        self.gpio_reset.write(True)

    def enable(self):
        if not self.gpio_enable: return
        self.gpio_enable.write(True)

    def disable(self):
        if not self.gpio_enable: return
        self.gpio_enable.write(False)

    @staticmethod
    def packet_from_data(data):
        numbers = struct.unpack('>16H', data)
        csum = sum(data[:-2])
        if csum != numbers[-1]:
            log.warn("Bad packet data: %s / %s", data, csum)
            return
        return Packet(*numbers[2:-2])

    def receive_one(self):
        while not self.stop.is_set():
            c = self.port.read(1)
            if not c or c != '\x42':
                continue
            c = self.port.read(1, .1)
            if not c or c != '\x4d':
                continue

            data = bytearray((0x42, 0x4d,))
            data += self.port.read(30, .1)
            if len(data) != 32:
                continue

            p = self.packet_from_data(data)
            if p: return p


def main():
    args = parser.parse_args()
    sensor = PMS5003(args.port, args.enable_pin, args.reset_pin)
    sensor.reset()
    start_at = time.time()
    try:
        while True:
            packet, now = sensor.receive_one(), time.time()
            log.info("@{: 6.2f}\t{: 6d}\t{: 6d}\t{: 6d}".format(
                    (now - start_at),
                    packet.pm01_atm, packet.pm25_atm, packet.concentration_unit))
    except KeyboardInterrupt:
        sensor.disable()
        log.info("Bye bye.")

if __name__ == "__main__":
    main()
