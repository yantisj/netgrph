#!/usr/bin/env python3
#
# Generate Neighbor Data from NetDB
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
parser = argparse.ArgumentParser(description='Generate ND Database')
parser.add_argument("-nf", metavar='neighbor_file', help="Neighbor Data from NetDB", type=str)
parser.add_argument("-of", metavar='outfile', help="Output File for CSV", type=str)
parser.add_argument("-debug", help="Set debugging level", type=int)

# Argument Reference
args = parser.parse_args()

DEBUG = 0
if args.debug: DEBUG = args.debug

def load_nd_file(fileName):

    nd = open(fileName, 'r')

    ndata = []

    for line in nd:
        if re.search('^\#', line ):
            continue

        line = line.strip()
        en = line.split(',')
        localName = en[0]
        localPort = en[1]
        remoteName = get_entry(en[2].split('.'))
        remotePort = en[6]

        # Save data to list
        ndline = "{0},{1},{2},{3}".format(localName,localPort,remoteName,remotePort)
        ndata.append(ndline)

    return ndata

def save_nd_data(ndata):

    save = open(args.of, "w")
    print("LocalName,LocalPort,RemoteName,RemotePort", file=save)

    print(*ndata, sep='\n', file=save)
    save.close()

def get_entry(l,pos=0):
    return l[pos]

## Process Arguments to generate output
if args.nf and args.of:

    ndata = load_nd_file(args.nf)
    save_nd_data(ndata)

# Print Help
else:
    parser.print_help()
    print()
