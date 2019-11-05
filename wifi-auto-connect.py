#!/usr/bin/env python3
import os, subprocess, logging, sys, time, argparse

poll_interval = 60 # How often to check for open networks?
min_signal_strength = 10 # Minimum signal strength for an open network to connect to.

# --------------------------------------------------------------------------------------------------

security_types = ['WPA1', 'WPA2', '802.1X', '--']
failed_networks = set()

"""
A signal wifi network for a single interface. Each network has a name, signal, and defines security.
"""
class WifiNetwork():
    def __init__(self, interface, parts):
        self.interface = interface
        sigval = parts[0]
        del(parts[0])
        self.security = []
        while len(parts) > 1 and parts[0] in security_types:
            if parts[0] != '--':
                self.security.append(parts[0])
            del(parts[0])
        self.ssid = ' '.join(parts)
        self.log = logging.getLogger(self.ssid)
        try:
            self.signal = int(sigval)
        except ValueError as verr:
            self.signal = -1
            self.log.error(f'signal was not an integer: {sigval}')
        self.log.debug(f'signal: {self.signal} security: {self.security}')

    # Attempt to connect to this WiFi network.
    def connect(self, password = ''):
        self.log.info('attempting to connect...')
        connect = f'connect "{self.ssid}"'
        if len(password) > 0:
            connect += f' password {password}'
        cmd = f'sudo nmcli device wifi {connect} ifname "{self.interface}"'
        self.log.info(cmd)
        res = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
        err = res.stderr.strip()
        if len(err) <= 0:
            return True

        self.log.warning(f'connection error: {err}')
        return False

"""
Ping a site with a specific interface. Returns the ms delay (or negative value upon failure).
"""
def ping(interface, ping_site = 'google.com', count = 5):
  ping_cmd = f'ping -I {interface} -c {count} {ping_site} | grep "packets transmitted"'
  res = subprocess.run(ping_cmd,shell=True,check=False,capture_output=True,text=True).stdout.strip()
  log.debug(f'interface {interface} ping for {ping_site}: {res}')
  parts = [x for x in res.split(" ") if len(x) > 0]
  if len(parts) <= 0: return -1
  ms = parts[len(parts) - 1]
  if not ms.endswith('ms'): return -2
  return int(ms[0:-2])

"""
Scans for networks (returns an array of WifiNetwork objects, sorted high->low signal).
"""
def scan(interface):
    scan_cmd = f'nmcli -f SIGNAL,SECURITY,SSID dev wifi list ifname {interface}'
    p = subprocess.Popen(scan_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    networks = []
    for line in p.stdout.readlines():
        line = line.decode('utf-8').strip()
        parts = [x for x in line.split(" ") if len(x) > 0]
        if len(parts) <= 0 or parts[0] == 'SIGNAL' or parts[len(parts)-1] == '--': continue
        networks.append(WifiNetwork(interface, parts))
    return sorted(networks, key=lambda x: x.signal, reverse=True)

"""
Attempt to connect to the highest-signal-strength open network.
Returns the WifiNetwork object upon success, otherwise None.
"""
def connect(interface):
    networks = scan(interface)
    open_networks = [n for n in networks if len(n.security) == 0]
    log.debug(f'found {len(open_networks)} open networks...')
    for network in open_networks:
        if network.signal <= min_signal_strength:
            network.log.debug('skipping (weak signal)')
            continue
        if network.ssid in failed_networks:
            network.log.debug('skipping (previously failed)')
            continue
        if not network.connect():
            failed_networks.add(network.ssid)
            continue
        tries = 0
        network.log.info(f'connection appeared to succeed; checking ping...')
        while tries < 10:
            ping_ms = ping(interface)
            if ping_ms >= 0:
                break
            time.sleep(1)
            tries += 1
        if ping_ms < 0:
            network.log.warning(f'connection faled (unable to ping)')
            failed_networks.add(network.ssid)
            continue
        else:
            network.log.info(f'successfully connected; ping: {ping_ms}')
            return network
    return None

if __name__ == "__main__":
    log_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

    parser = argparse.ArgumentParser()
    parser.add_argument('interface', default=os.getenv('WIFI_AUTO_CONNECT_INTERFACE', 'wlan0'))
    parser.add_argument('--log-level', '-l', choices=log_levels, default='INFO', help='logging level')
    parser.add_argument('--log-format', '-f', default='[%(levelname)s] [%(name)s] %(message)s')
    opts = parser.parse_args()

    logging.basicConfig(format=opts.log_format, level=opts.log_level)
    log = logging.getLogger(opts.interface)

    cmd = f'ifconfig {opts.interface} | grep \'inet\' || echo ""'
    while True:
        res = subprocess.run(cmd,shell=True,check=True,capture_output=True,text=True).stdout.strip()
        ping_ms = -1
        if len(res) > 0:
            ip = res.split(' ')[1]
            ping_ms = ping(interface)
            if ping_ms >= 0:
                log.info(f'already connected; ip: {ip}; ping: {ping_ms}')
            else:
                log.info(f'already connected, but no internet connection.')
        if ping_ms < 0:
            connect(opts.interface)
        log.debug(f'sleeping for {poll_interval}s')
        time.sleep(poll_interval)