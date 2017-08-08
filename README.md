# PMS5003 Logger

Simple Python app to collect data from PMS5003 by Plantower. Originally written by kzyapkov see https://github.com/kzyapkov/pms5003-logger

Added possibility to send data to Domoticz.

```
user@raspberry:~/pms5003-logger$ ./pmlog.py domoticz -h
usage: pmlog.py domoticz [-h] -ip IP_ADDRESS [-p DOMOTICZ_PORT]
                         [-m {oneshot,monitor}]
                         [--measure-period MEASURE_PERIOD]
                         [--pm_1_idx PM_1_IDX] [--pm_25_idx PM_25_IDX]
                         [--pm_10_idx PM_10_IDX]
                         [--pm_1_percent_idx PM_1_PERCENT_IDX]
                         [--pm_25_percent_idx PM_25_PERCENT_IDX]
                         [--pm_10_percent_idx PM_10_PERCENT_IDX]

optional arguments:
  -h, --help            show this help message and exit
  -ip IP_ADDRESS, --ip_address IP_ADDRESS
                        IP address of domoticz server
  -p DOMOTICZ_PORT, --domoticz_port DOMOTICZ_PORT
                        Port of domoticz server
  -m {oneshot,monitor}, --mode {oneshot,monitor}
                        Monitor or oneshot mode
  --measure-period MEASURE_PERIOD
                        Seconds between measurements
  --pm_1_idx PM_1_IDX   IDX of PM1 - if empty nothing will be reported to
                        domoticz
  --pm_25_idx PM_25_IDX
                        IDX of PM2.5 - if empty nothing will be reported to
                        domoticz
  --pm_10_idx PM_10_IDX
                        IDX of PM10 - if empty nothing will be reported to
                        domoticz
  --pm_1_percent_idx PM_1_PERCENT_IDX
                        IDX of PM1 percent - if empty nothing will be reported
                        to domoticz
  --pm_25_percent_idx PM_25_PERCENT_IDX
                        IDX of PM2.5 percent - if empty nothing will be
                        reported to domoticz
  --pm_10_percent_idx PM_10_PERCENT_IDX
                        IDX of PM10 percent - if empty nothing will be
                        reported to domoticz

Example usage:
Monitor mode (for systemd service):
sudo python ./pmlog.py  -p /dev/ttyAMA0 --enable-pin 24 --warmup-time 30 domoticz -ip 192.168.1.1 -p 8080 -m monitor --measure-period 300  --pm_1_idx 10 --pm_25_idx 11 --pm_10_idx 12 --pm_1_percent_idx 13 --pm_25_percent_idx 14 --pm_10_percent_idx 15

Oneshot mode (for crontab):
sudo python ./pmlog.py  -p /dev/ttyAMA0 --enable-pin 24 --warmup-time 30 domoticz -ip 192.168.1.1 -p 8080 -m oneshot --pm_1_idx 10 --pm_25_idx 11 --pm_10_idx 12 --pm_1_percent_idx 13 --pm_25_percent_idx 14 --pm_10_percent_idx 15
Crontab example:
*/30 * * * * sudo /usr/bin/python /opt/domoticz/scripts/pmlog.py  -p /dev/ttyAMA0 --enable-pin 24 --warmup-time 30 domoticz -ip 192.168.1.1 -p 8080 -m monitor --measure-period 300  --pm_1_idx 10 --pm_25_idx 11 --pm_10_idx 12 --pm_1_percent_idx 13 --pm_25_percent_idx 14 --pm_10_percent_idx 15
```
