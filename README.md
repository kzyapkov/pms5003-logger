# PMS5003 Logger

Simple Python app to collect data from PMS5003 by Plantower. Originally written by kzyapkov see https://github.com/kzyapkov/pms5003-logger

It has option to send data to Domoticz.

[Instrukcja (po polsku)](https://github.com/mstojek/pms5003-logger/wiki/Raspberry-Pi-i-Domoticz-=-monitorowanie-poziomu-py%C5%82u-PM10-i-PM2.5-za-pomoc%C4%85-czujnika-PMS5003)

Help fragment:  

```
osmc@osmc:~/git/pms5003-logger$ ./pmlog.py domoticz -h
usage: pmlog.py domoticz [-h] -ip IP_ADDRESS [-p PORT] [-m {oneshot,monitor}]
                         [--measure-period MEASURE_PERIOD]
                         [--pm_1_idx PM_1_IDX] [--pm_25_idx PM_25_IDX]
                         [--pm_10_idx PM_10_IDX]
                         [--pm_1_percent_idx PM_1_PERCENT_IDX]
                         [--pm_25_percent_idx PM_25_PERCENT_IDX]
                         [--pm_10_percent_idx PM_10_PERCENT_IDX]

optional arguments:
  -h, --help            show this help message and exit
  -ip IP_ADDRESS, --domoticz-ip IP_ADDRESS
                        IP address of domoticz server
  -p PORT, --domoticz-port PORT  Port of domoticz server
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
                        IDX of PM1 percent (100% is 25 ug/m3) - if empty
                        nothing will be reported to domoticz
  --pm_25_percent_idx PM_25_PERCENT_IDX
                        IDX of PM2.5 percent (100% is 25 ug/m3) - if empty
                        nothing will be reported to domoticz
  --pm_10_percent_idx PM_10_PERCENT_IDX
                        IDX of PM10 percent (100% is 50 ug/m3) - if empty
                        nothing will be reported to domoticz
osmc@osmc:~/git/pms5003-logger$


Example usage:
Monitor mode (for systemd service):
sudo python ./pmlog.py  -p /dev/ttyAMA0 --enable-pin 24 --warmup-time 30 domoticz -ip 192.168.1.1 -p 8080 -m monitor --measure-period 300  --pm_1_idx 10 --pm_25_idx 11 --pm_10_idx 12 --pm_1_percent_idx 13 --pm_25_percent_idx 14 --pm_10_percent_idx 15

Oneshot mode (for crontab):
sudo python ./pmlog.py  -p /dev/ttyAMA0 --enable-pin 24 --warmup-time 30 domoticz -ip 192.168.1.1 -p 8080 -m oneshot --pm_1_idx 10 --pm_25_idx 11 --pm_10_idx 12 --pm_1_percent_idx 13 --pm_25_percent_idx 14 --pm_10_percent_idx 15
Crontab example:
*/30 * * * * sudo /usr/bin/python /opt/domoticz/scripts/pmlog.py  -p /dev/ttyAMA0 --enable-pin 24 --warmup-time 30 domoticz -ip 192.168.1.1 -p 8080 -m monitor --measure-period 300  --pm_1_idx 10 --pm_25_idx 11 --pm_10_idx 12 --pm_1_percent_idx 13 --pm_25_percent_idx 14 --pm_10_percent_idx 15
```
