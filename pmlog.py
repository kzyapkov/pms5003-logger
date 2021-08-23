#!/usr/bin/python
import sys
import os
import time
import signal
import struct
import logging
import argparse
from collections import namedtuple
from threading import Event

from periphery import GPIO, Serial

import urllib
import urllib2

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr,
                    format='%(asctime)-15s %(levelname)-8s %(message)s')
log = logging.getLogger()

parser = argparse.ArgumentParser(description='PMS5003 data logger')
parser.add_argument(
    "-p", "--serial-port", type=str, default="/dev/ttyS1",
    help="Serial port connected to the PMS5003 sensor")
parser.add_argument(
    "--reset-pin", type=int, default=None,
    help="GPIO number connected to the RESET signal")
parser.add_argument(
    "--enable-pin", type=int, default=None,
    help="GPIO number connected to the SET (enable) signal")
parser.add_argument(
    "--warmup-time", type=int, default=30,
    help="Seconds to wait before reading data")

subparsers = parser.add_subparsers(dest="cmd")

cmd_monitor_parser = subparsers.add_parser("monitor")

cmd_monitor_parser.add_argument(
    "--measure-period", type=int, default=60 * 5,
    help="Seconds between measurements")

cmd_oneshot_parser = subparsers.add_parser("oneshot")

cmd_domoticz_parser = subparsers.add_parser("domoticz")
cmd_domoticz_parser.add_argument(
    "-ip", "--domoticz-ip", required=True,
    help="IP address of domoticz server")
cmd_domoticz_parser.add_argument(
    "-p", "--domoticz-port", default=8080,
    help="Port of domoticz server")
cmd_domoticz_parser.add_argument(
    "-m", "--mode", default='oneshot', choices=['oneshot', 'monitor'],
    help="Monitor or oneshot mode")
cmd_domoticz_parser.add_argument(
    "--measure-period", type=int, default=60 * 5,
    help="Seconds between measurements")
cmd_domoticz_parser.add_argument(
    "--pm_1_idx",
    help="IDX of PM1 - if empty nothing will be reported to domoticz")
cmd_domoticz_parser.add_argument(
    "--pm_25_idx",
    help="IDX of PM2.5 - if empty nothing will be reported to domoticz")
cmd_domoticz_parser.add_argument(
    "--pm_10_idx",
    help="IDX of PM10 - if empty nothing will be reported to domoticz")
cmd_domoticz_parser.add_argument(
    "--pm_1_percent_idx",
    help="IDX of PM1 percent (100%% is 25 ug/m3) - if empty nothing will be reported to domoticz")
cmd_domoticz_parser.add_argument(
    "--pm_25_percent_idx",
    help="IDX of PM2.5 percent (100%% is 25 ug/m3) - if empty nothing will be reported to domoticz")
cmd_domoticz_parser.add_argument(
    "--pm_10_percent_idx",
    help="IDX of PM10 percent (100%% is 50 ug/m3) - if empty nothing will be reported to domoticz")

Packet = namedtuple('Packet', [
    'pm1_std', 'pm25_std', 'pm10_std', 'pm01_atm', 'pm2_5_atm',
    'pm10_atm', 'count_03um', 'count_05um', 'count_1um',
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
        log.info("Enable sensor (via gpio %s)", self.gpio_enable.line)
        self.gpio_enable.write(True)

    def disable(self):
        if not self.gpio_enable: return
        log.info("Disable sensor (via gpio %s)", self.gpio_enable.line)
        self.gpio_enable.write(False)

    def discard_input(self):
        while self.port.input_waiting(): self.port.read(4096, 0)

    def warmup(self, seconds):
        log.info("Warming up for %s seconds", seconds)
        self.stop.wait(seconds)
        self.discard_input()

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


def run_monitor(sensor, args):
    start_at = time.time()
    sleep_period = args.measure_period - args.warmup_time
    if args.enable_pin:
        sensor.enable()
    if args.warmup_time:
        sensor.warmup(args.warmup_time)
    try:
        while not sensor.stop.is_set():
            packet = sensor.receive_one()
            if not packet: break
            packet_at = time.time()
            log.info("@{: 6.2f}\t{}".format((packet_at - start_at), packet))
            if args.cmd == "domoticz":
                report_to_domoticz(packet, args)
            if sleep_period > 0:
                sensor.disable()
                sensor.stop.wait(sleep_period)
                if sensor.stop.is_set(): break
                sensor.reset()
                sensor.enable()
                sensor.warmup(args.warmup_time)
            else:
                sensor.stop.wait(args.measure_period)
    except KeyboardInterrupt:
        log.info("Bye bye.")
    finally:
        sensor.disable()


def run_oneshot(sensor, args):
    if args.enable_pin:
        sensor.enable()
    if args.warmup_time:
        sensor.warmup(args.warmup_time)
    try:
        packet = sensor.receive_one()
        log.info("{}".format(packet))
        if args.cmd == "domoticz":
            report_to_domoticz(packet, args)
    except KeyboardInterrupt:
        log.info("Bye bye.")
    finally:
        sensor.disable()
    sensor.disable()


def install_signal_handlers(sensor):
    def _sighandler(signum, frame):
        log.info("Got %s", signum)
        sensor.stop.set()

    signal.signal(signal.SIGINT, _sighandler)
    signal.signal(signal.SIGTERM, _sighandler)


def report_to_domoticz(packet, args):
    if args.pm_1_idx:
        send_http_request_to_domoticz(ip=args.domoticz_ip, port=args.domoticz_port, idx=args.pm_1_idx, idx_value=packet.pm01_atm)
    if args.pm_25_idx:
        send_http_request_to_domoticz(ip=args.domoticz_ip, port=args.domoticz_port, idx=args.pm_25_idx,
                                      idx_value=packet.pm2_5_atm)
    if args.pm_10_idx:
        send_http_request_to_domoticz(ip=args.domoticz_ip, port=args.domoticz_port, idx=args.pm_10_idx, idx_value=packet.pm10_atm)
    if args.pm_1_percent_idx:
        send_http_request_to_domoticz(ip=args.domoticz_ip, port=args.domoticz_port, idx=args.pm_1_percent_idx,
                                      idx_value=packet.pm01_atm * 4)
    if args.pm_25_percent_idx:
        send_http_request_to_domoticz(ip=args.domoticz_ip, port=args.domoticz_port, idx=args.pm_25_percent_idx,
                                      idx_value=packet.pm2_5_atm * 4)
    if args.pm_10_percent_idx:
        send_http_request_to_domoticz(ip=args.domoticz_ip, port=args.domoticz_port, idx=args.pm_10_percent_idx,
                                      idx_value=packet.pm10_atm * 2)


def send_http_request_to_domoticz(ip, port, idx, idx_value):
    url = "http://" + ip + ":" + port + "/json.htm?type=command&param=udevice&nvalue=0&idx=" + str(
        idx) + "&svalue=" + str(idx_value)
    # print(url)
    request = urllib2.Request(url)
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
        log.info('HTTPError = ' + str(e.code))
    except urllib2.URLError, e:
        log.info('URLError = ' + str(e.reason))
    # except httplib.HTTPException, e:
    #    log.info('HTTPException')
    except Exception:
        import traceback
        log.info('generic exception: ' + traceback.format_exc())


def main():
    args = parser.parse_args()
    sensor = PMS5003(args.serial_port, args.enable_pin, args.reset_pin)
    sensor.reset()

    install_signal_handlers(sensor)

    if args.cmd == "monitor":
        run_monitor(sensor, args)
    elif args.cmd == "oneshot":
        run_oneshot(sensor, args)
    elif args.cmd == "domoticz":
        if args.mode == "monitor":
            run_monitor(sensor, args)
        elif args.mode == "oneshot":
            run_oneshot(sensor, args)


if __name__ == "__main__":
    main()
