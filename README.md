# WiFi Auto Connect
A script/service to automatically connect to open WiFi networks.

## Motivation
Useful for [internet bonding attempting to minimize cellular data](https://www.technicallywizardry.com/internet-bonding-raspberry-pi-access-point/), especially when mobile (i.e., in a car) and when other forms of security (i.e., VPN) obviate security concerns.

## Limitations
Cannot connect to networks which require web-based acceptance of terms (pressing "Okay" or "Continue," such as Starbucks). If you know how to achieve this, please let me know.

## Issues?
Please open a Github issue.

# Instructions

## Pre-Requisites

- Python3
- `nmcli`

## Install

Clone or download this git repository.

## Test Run

Assuming you cloned the git repository into `/home/pi/wifi-auto-connect` and you wish to auto-connect via the adapter `wlan0`:
```
chmod +x /home/pi/wifi-auto-connect/wifi-auto-connect.py
/home/pi/wifi-auto-connect/wifi-auto-connect.py wlan0 -l DEBUG
```

You may omit the `-l DEBUG` parameter if desired (this parameter accepts standard Python `logging` levels).

## Additiontal Options

Blacklist specific SSIDs (separated by commas): `--blacklist network_ssid,other_SSID`

## Install the Service

First, modify the `wifi-auto-connect.service` file such that the ExecStart command matches the command per the above `Test Run`.

```
sudo cp ./wifi-auto-connect.service /etc/systemd/system/wifi-auto-connect.service
sudo systemctl start wifi-auto-connect
sudo systemctl enable wifi-auto-connect
```
