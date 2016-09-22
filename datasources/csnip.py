#!/usr/bin/env python3
#
# Generate Config Snippets from Cisco Devices
#
# Copyright (c) 2016 "Jonathan Yantis"
#
# This file is a part of NetGrph.
#
#    This program is free software: you can redistribute it and/or  modify
#    it under the terms of the GNU Affero General Public License, version 3,
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    As a special exception, the copyright holders give permission to link the
#    code of portions of this program with the OpenSSL library under certain
#    conditions as described in each individual source file and distribute
#    linked combinations including the program with the OpenSSL library. You
#    must comply with the GNU Affero General Public License in all respects
#    for all of the code used other than as permitted herein. If you modify
#    file(s) with this exception, you may extend this exception to your
#    version of the file(s), but you are not obligated to do so. If you do not
#    wish to do so, delete this exception statement from your version. If you
#    delete this exception statement from all source files in the program,
#    then also delete it in the license file.
#
#
import sys
import re
import argparse
import csv
from ciscoconfparse import CiscoConfParse

# Config Options
conf_dir = "/tftpboot/"
extension = "-confg"

# Argument Parser
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description='Generate Cisco Snippets')
parser.add_argument("switch", help="Switch to get snippet from",
                    type=str)
parser.add_argument("-int", metavar="interface",
                    help="Interface (switchport or VLAN) to pull config from",
                    type=str)
parser.add_argument('-match', metavar='string',
                    help='Match a string on an interface',
                    type=str)
parser.add_argument("-debug", help="Set debugging level", type=int)

# Argument Reference
args = parser.parse_args()


DEBUG = 0
if args.debug: DEBUG = args.debug


def get_int(switch, interface):
    """ Get a config snippet from a device """

    conf_file = conf_dir + switch + extension

    interface = expand_port(interface)

    try:
        parse = CiscoConfParse(conf_file)
    except:
        print("Error: could not load config for ", conf_file)
        sys.exit(1)

    search_int = "^interface " + interface + "$"



    if args.match:
        m = parse.find_objects_w_child(parentspec=search_int,
            childspec=args.match)
        if m:
            print(args.switch + ',' + args.int + ',' + args.match)

    else:
        iface = parse.find_all_children(search_int)
        if iface:
            print('!' + switch + ' ' + interface)
        for line in iface:
            print(line)
        if iface:
            print('!')


def normalize_port(port):
    """Normalize Ports (GigabitEthernet1/1 -> Gi1/1)"""


    port = port.replace('interface ', '')
    port = port.replace('TenGigabitEthernet', 'Te')
    port = port.replace('GigabitEthernet', 'Gi')
    port = port.replace('FastEthernet', 'Fa')
    port = port.replace('Ethernet', 'Eth')
    port = port.replace('v', 'Vlan')
    port = port.replace('vlan', 'Vlan')

    return port

def expand_port(port):

    port = port.title()

    port = re.sub(r'^Gi(\d+)', r'GigabitEthernet\1', port)
    port = re.sub(r'^Te(\d+)', r'TenGigabitEthernet\1', port)
    port = re.sub(r'^Fa(\d+)', r'FastEthernet\1', port)
    port = re.sub(r'^Eth(\d+)', r'Ethernet\1', port)
    port = re.sub(r'^E(\d+)', r'Ethernet\1', port)
    port = re.sub(r'^Po(\d+)', r'Port-channel\1', port)

    return port

## Process Arguments to generate output
# Got VLAN Range and Switch Name
if args.switch and args.int:

    get_int(args.switch, args.int)

# Print Help
else:
    parser.print_help()
    print()
