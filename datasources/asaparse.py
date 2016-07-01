#!/usr/bin/env python3
#
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
"""Parse ASA Config Files for NetGrph Data"""

import sys
import os
import re
import argparse
import socket
import csv
import ipaddress
import logging
from ciscoconfparse import CiscoConfParse

logger = logging.getLogger(__name__)


# Config Options

fwdir = "/tftpboot/asafw/"
extension = ".cfg"

# Argument Parser
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description='Generate Cisco ASA Configuration Details')

parser.add_argument("-fd", metavar='asafwfile', help="ASA FW Device file", type=str)
parser.add_argument("-ffile", metavar='outfile', help="NetGrph Firewall File", type=str)
parser.add_argument("-debug", help="Set debugging level", type=int)

# Argument Reference
args = parser.parse_args()

DEBUG = 0
if args.debug: DEBUG = args.debug


def load_fwfile(fw_file):
    """Import ASA CSV Configuration File"""

    logger.debug("Importing Firewalls from " + fw_file)

    f = open(fw_file, 'r')
    fwdb = csv.DictReader(f)

    fwimport = []

    for en in fwdb:
        asafile = fwdir + en['FW'] + extension

        if os.path.exists(asafile):
            logger.debug("Found ASA File: " + asafile)

            fwints = process_asa_file(asafile, en)
            fwimport.append(fwints)

        else:
            logger.error("Could not find ASA file: " + asafile)

    return fwimport


def process_asa_file(asafile, en):
    """Go through individual ASA Configuration Looking for Interfaces to import"""

    f = open(asafile)

    fwints = []
    instance = en['FW']

    instance = instance.title()
    instance = instance + "FW"

    inside = None
    intVlan = None
    desc = None
    seclevel = None
    ip = None

    for line in f:
        line = line.strip()
        ivlan = re.search(r'interface (Vlan\d+)', line)
        rdesc = re.search(r'^description ', line)
        rsec = re.search(r'^security-level (\d+)', line)

        if inside and re.search('^!', line):
            logger.debug("FW Found Ints: %s , %s , %s , %s , %s , %s , %s",
                         instance, intVlan, desc, seclevel, ip, en['hostname'],
                         en['logIndex'])

            fwints.append("{0},{1},{2},{3},{4},{5},{6}".format(
                instance, intVlan, desc, seclevel, ip, en['hostname'], en['logIndex']))

            inside = None
            intVlan = None
            desc = None
            seclevel = None
            ip = None

        if ivlan:
            inside = 1
            intVlan = ivlan.group(1)
        elif inside and rdesc:
            desc = line
            desc = desc.replace('description ', '')
        elif inside and rsec:
            seclevel = rsec.group(1)

    # Return found ints
    return fwints


# Write results to file
def save_fw_file(data, out_file):

    save = open(out_file, "w")
    print("Name,Interface,Description,Security-Level,IP,Hostname,Log-Index", file=save)

    for fw in data:
        for entry in fw:
            print(entry, file=save)
    save.close()


## Process Arguments to generate output
# Got VLAN Range and Switch Name
if args.fd and args.ffile:

    loglevel = logging.INFO

    if DEBUG:
        loglevel = logging.DEBUG

    logging.basicConfig(format='%(asctime)s %(name)s:%(levelname)s: %(message)s',
                        stream=sys.stdout, level=loglevel)

    # Load FW Data
    fwimport = load_fwfile(args.fd)

    # Save FW Data
    save_fw_file(fwimport, args.ffile)


# Print Help
else:
    parser.print_help()
    print()
