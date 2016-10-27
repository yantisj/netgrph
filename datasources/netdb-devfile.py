#!/usr/bin/env python3
#
# Generate Device File from NetDB
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
import socket

# Config Options
configDir = "/opt/netdb/data/"

# Argument Parser
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description='Generate Devicefile Database')
parser.add_argument("-df", metavar='neighbor_file', help="devicefile.csv from NetDB", type=str)
parser.add_argument("-of", metavar='outfile', help="Output File for CSV", type=str)
parser.add_argument("-debug", help="Set debugging level", type=int)

# Argument Reference
args = parser.parse_args()

DEBUG = 0
if args.debug: DEBUG = args.debug

def load_nd_file(fileName):

    df = open(fileName, 'r')

    devdata = []

    for line in df:
        if re.search('^\#', line ):
            continue

        line = line.strip()
        en = line.split(',')

        device = get_entry(en[0].split('.'))
        fqdn   = en[0]
        mgmt   = None
        dtype = "Switch"
        platform = 'cisco_ios'

        for e in en:
            # Device Flags
            mg      = re.search('mgmtgroup\=(\w+)', e)
            arp     = re.search('^(arp|netdbarp)$', e)
            standby = re.search('^(standby)$', e)
            p = re.search('devtype\=(\w+)', e)
            if mg:
                mgmt = mg.group(1)
            elif arp:
                dtype = "Primary"
            elif standby:
                dtype = "Standby"
            elif p:
                #print(p.group(1))
                platform = tr_devtype(p.group(1))

        #print(router)
        #print(en)

        dev = ("{0},{1},{2},{3},{4}").format(device,fqdn,mgmt,dtype,platform)
        devdata.append(dev)

    return devdata

def tr_devtype(dt):
    """Translation NetDB devtype to Netmiko"""
    if dt == 'nxos':
        dt = 'cisco_nxos'
    elif dt == 'asa':
        dt = 'cisco_asa'

    return dt


def save_nd_data(ndata):

    save = open(args.of, "w")
    print("Device,FQDN,MgmtGroup,Type,Platform", file=save)

    print(*ndata, sep='\n', file=save)
    save.close()

def get_entry(l,pos=0):
    return l[pos]

## Process Arguments to generate output
if args.df and args.of:

    devdata = load_nd_file(args.df)
    save_nd_data(devdata)

# Print Help
else:
    parser.print_help()
    print()
