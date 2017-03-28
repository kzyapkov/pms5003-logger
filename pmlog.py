#!/usr/bin/python
import sys
import os
import time
import struct
from collections import namedtuple
from threading import Event
import logging

from periphery import GPIO, Serial

enable_gpio = 7
reset_gpio = 19
serial_port = '/dev/ttyS1'

Packet = namedtuple('Packet', [
        'pm1_std', 'pm25_std', 'pm10_st', 'pm01_atm', 'pm25_atm',
        'concentration_unit', 'count_03um', 'count_05um', 'count_1um',
        'count_2_5u', 'count_5um', 'count_10um'])


class PMS5003(object):
    def __init__(self, port, enable_pin=None, reset_pin=None):
        self.port = port
        self.gpio_enable = None
        self.gpio_reset = None
        self.stop = Event()

        # suspend sensor by default
        if enable_pin is not None:
            self.gpio_enable = GPIO(enable_pin, "low")

        if reset_pin is not None:
            self.gpio_reset = GPIO(reset_pin, "high")

    def reset(self):
        if self.gpio_reset is None:
            return

        self.gpio_reset.write(False)
        self.enable()
        time.sleep(.1)
        self.gpio_reset.write(True)

    def enable(self):
        self.gpio_enable.write(True)

    def disable(self):
        self.gpio_enable.write(False)

    @staticmethod
    def packet_from_data(data):
        numbers = struct.unpack('>16H', data)
        csum = sum(data[:-2])
        if csum != numbers[-1]:
            #print(packet)
            #print(csum)
            #print(packet[-1])
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
    p = Serial(serial_port, 9600)
    sensor = PMS5003(p, enable_gpio, reset_gpio)
    sensor.reset()
    start_at = time.time()
    try:
        while True:
            packet, now = sensor.receive_one(), time.time()
            print("@{: 6.2f}\t{: 6d}\t{: 6d}\t{: 6d}".format(
                    (now - start_at),
                    packet.pm01_atm, packet.pm25_atm, packet.concentration_unit))
    except KeyboardInterrupt:
        sensor.disable()
        print("Bye bye.")

if __name__ == "__main__":
    main()
