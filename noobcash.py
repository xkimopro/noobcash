#!/usr/bin/python3

import argparse, os, re , socket

def getAllLanIPs():
    full_results = [re.findall('^[\w\?\.]+|(?<=\s)\([\d\.]+\)|(?<=at\s)[\w\:]+', i) for i in os.popen('arp -a')]
    final_results = [dict(zip(['HOSTNAME', 'LAN_IP', 'MAC_ADDRESS'], i)) for i in full_results]
    final_results = [{**i, **{'LAN_IP':i['LAN_IP'][1:-1]}} for i in final_results]
    return [  f['LAN_IP'] for f in final_results ]


print(getAllLanIPs())

parser = argparse.ArgumentParser(description='Noobcash arguments helper')
parser.add_argument('--localnet', dest='localnet', action='store_true')
parser.set_defaults(localnet=False)

arg_localnet = parser.parse_args().localnet

if arg_localnet:

else:
