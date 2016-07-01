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
"""ngreport Generates Reports from the NetGrph Database"""
import os
import re
import argparse
import nglib

# Default Config File Location
config_file = '/etc/netgrph.ini'

# Test/Dev Config
dirname = os.path.dirname(os.path.realpath(__file__))
if re.search(r'\/dev$', dirname):
    config_file = 'netgrphdev.ini'
elif re.search(r'\/test$', dirname):
    config_file = "netgrphtest.ini"

parser = argparse.ArgumentParser()

parser = argparse.ArgumentParser(prog='ngreport',
                                 description='Generate Reports from NetGrph')

parser.add_argument("-vrf", metavar='name', help="Generate a Report on a VRF",
                    type=str)
parser.add_argument("-vrfs", help="VRF Report on all VRFs",
                    action="store_true")
parser.add_argument("-vlans", help="VLAN ID Report (combine with -vra and -e)",
                    action="store_true")

parser.add_argument("-vrange", metavar='1[-4096]', help="VLAN Range (default 1-1999)",
                    type=str)
parser.add_argument("-dev", metavar=".*", help="Report on Network Devices in regex",
                    type=str)
parser.add_argument("-output", metavar='TREE',
                    help="Return Format: TREE, TABLE, CSV, JSON, YAML", type=str)
parser.add_argument("-empty",
                    help="Only Return Empty VLANs (requires NetDB)",
                    action="store_true")
parser.add_argument("--conf", metavar='file', help="Alternate Config File", type=str)
parser.add_argument("--debug", help="Set debugging level", type=int)
parser.add_argument("--verbose", help="Verbose Output", action="store_true")

args = parser.parse_args()

# Alternate Config File
if args.conf:
    config_file = args.conf

verbose = 0
if args.verbose:
    verbose = 1
if args.debug:
    verbose = args.debug

# Default VLAN Range
if not args.vrange:
    args.vrange = "1-1999"
if args.output:
    args.output = args.output.upper()

# Setup Globals in hwinvmod
nglib.verbose = verbose
nglib.query.verbose = verbose
nglib.query.vlan.verbose = verbose

# Initialize Library
nglib.init_nglib(config_file)

if args.vlans:
    report = "full"
    if args.empty:
        report = "empty"

    rtype = "TREE"
    if args.output:
        rtype = args.output

    nglib.report.get_vlan_report(args.vrange, report=report, rtype=rtype)


else:
    parser.print_help()
    print()
