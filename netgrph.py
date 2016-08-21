#!/usr/bin/env python3
#
# NetGrph Database CLI Query Tool
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
"""netgrph is the primary CLI query too for NetGrph
   Also see ngreport
"""
import os
import re
import argparse
import nglib
import nglib.query


# Default Config File Location
config_file = '/etc/netgrph.ini'
alt_config = './docs/netgrph.ini'

# Test/Dev Config
dirname = os.path.dirname(os.path.realpath(__file__))
if re.search(r'\/dev$', dirname):
    config_file = 'netgrphdev.ini'
elif re.search(r'\/test$', dirname):
    config_file = "netgrphdev.ini"

parser = argparse.ArgumentParser()

parser = argparse.ArgumentParser(prog='netgrph',
                                 description='Query the NetGrph Database',
                                 epilog="""
                                 Examples:
                                 netgrph 10.1.1.1 (Free Search for IP),
                                 netgrph -net 10.1.1.0/24 (Search for CIDR),
                                 netgrph -group MDC (VLAN Database Search),
                                 netgrph -fp 10.1.1.1 10.2.2.1 (Firewall Path Search)
                                 """)

parser.add_argument("search", help="Search the NetGrph Database (Wildcard Default)",
                    type=str)
parser.add_argument("-ip", help="Network Details for an IP",
                    action="store_true")
parser.add_argument("-net", help="All networks within a CIDR (eg. 10.0.0.0/8)",
                    action="store_true")
parser.add_argument("-nlist", help="Get all networks in an alert group",
                    action="store_true")
parser.add_argument("-nfilter", help="Get all networks on a filter (see netgrph.ini)",
                    action="store_true")
parser.add_argument("-dev", help="Get the Details for a Device (Switch/Router/FW)",
                    action="store_true")
parser.add_argument("-path", metavar="src",
                    help="Full Path Between -p src dst (ip/cidr, requires NetDB)",
                    type=str)
parser.add_argument("-fpath", metavar="src",
                    help="Security Path between -fp src dst",
                    type=str)
parser.add_argument("-rpath", metavar="src",
                    help="Routed Path between -rp IP/CIDR1 IP/CIDR2 ",
                    type=str)
parser.add_argument("-spath", metavar="src",
                    help="Switched Path between -sp sw1 sw2 (Neo4j Regex)",
                    type=str)
parser.add_argument("-group", help="Get VLANs for a Management Group",
                    action="store_true")
parser.add_argument("-vrange", metavar='1[-4096]', help="VLAN Range (default 1-1999)",
                    type=str)
parser.add_argument("-vid", help="VLAN ID Search", action="store_true")
parser.add_argument("-vtree", help="Get the VLAN Tree for a VNAME",
                    action="store_true")
parser.add_argument("-output", metavar='TREE',
                    help="Return Format: TREE, TABLE, CSV, JSON, YAML", type=str)
parser.add_argument("--days", metavar='int', help="Days in Past (NetDB Specific)", type=int)
parser.add_argument("--conf", metavar='file', help="Alternate Config File", type=str)
parser.add_argument("--debug", help="Set debugging level", type=int)
parser.add_argument("--verbose", help="Verbose Output", action="store_true")

args = parser.parse_args()

# Alternate Config File
if args.conf:
    config_file = args.conf

# Test configuration exists
if not os.path.exists(config_file):
    if not os.path.exists(alt_config):
        raise Exception("Configuration File not found", config_file)
    else:
        config_file = alt_config

verbose = 0
if args.verbose:
    verbose = 1
if args.debug:
    verbose = args.debug

# 7 day default for NetDB
if not args.days:
    args.days = 7

# Default VLAN Range
if not args.vrange:
    args.vrange = "1-1999"
if args.output:
    args.output = args.output.upper()

# Setup Globals for Debugging
nglib.verbose = verbose

# Initialize Library
nglib.init_nglib(config_file)

if args.fpath:
    nglib.query.path.get_fw_path(args.fpath, args.search)

elif args.spath:
    rtype = "TREE"
    if args.output:
        rtype = args.output
    nglib.query.path.get_switched_path(args.spath, args.search, rtype=rtype)

elif args.rpath:
    rtype = "TREE"
    if args.output:
        rtype = args.output
    nglib.query.path.get_routed_path(args.rpath, args.search, rtype=rtype)
elif args.path:
    rtype = "TREE"
    if args.output:
        rtype = args.output
    nglib.query.path.get_full_path(args.path, args.search, rtype=rtype)

elif args.dev:
    rtype = "TREE"
    if args.output:
        rtype = args.output
    nglib.query.dev.get_device(args.search, rtype=rtype, vrange=args.vrange)

elif args.ip:
    rtype = "TREE"
    if args.output:
        rtype = args.output

    nglib.query.net.get_net(args.search, rtype=rtype, days=args.days)

elif args.net:
    rtype = "CSV"
    if args.output:
        rtype = args.output
    nglib.query.net.get_networks_on_cidr(args.search, rtype=rtype)

elif args.nlist:
    rtype = "CSV"
    if args.output:
        rtype = args.output
    nglib.query.net.get_networks_on_filter(args.search, rtype=rtype)

elif args.nfilter:
    rtype = "CSV"
    if args.output:
        rtype = args.output
    nglib.query.net.get_networks_on_filter(nFilter=args.search, rtype=rtype)

elif args.group:
    nglib.query.vlan.get_vlans_on_group(args.search, args.vrange)

elif args.vtree:
    rtype = "TREE"
    if args.output:
        rtype = args.output
    nglib.query.vlan.get_vtree(args.search, rtype=rtype)

elif args.vid:
    rtype = "TREE"
    if args.output:
        rtype = args.output
    nglib.query.vlan.search_vlan_id(args.search, rtype=rtype)

# Universal Search
elif args.search:

    # Try VLAN ID First
    # try:
    #     #vid = int(args.search)
    #
    #     if vid >= 0 and vid <= 4096:
    #         rtype = "TREE"
    #         if args.output: rtype = args.output
    #         nglib.query.searchVLANID(args.search,rtype=rtype)
    # except:
    vid = re.search(r'^(\d+)$', args.search)
    vname = re.search(r'^(\w+\-\d+)$', args.search)
    ip = re.search(r'^(\d+\.\d+\.\d+\.\d+)$', args.search)
    net = re.search(r'^(\d+\.\d+\.\d+\.\d+\/\d+)$', args.search)
    text = re.search(r'^(\w+)$', args.search)

    if vid:
        try:
            if int(args.search) >= 0 and int(args.search) <= 4096:
                rtype = "TREE"
                if args.output:
                    rtype = args.output
                nglib.query.vlan.search_vlan_id(args.search, rtype=rtype)
        except:
            pass
    elif vname:
        rtype = "TREE"
        if args.output:
            rtype = args.output
        nglib.query.vlan.get_vtree(args.search, rtype=rtype)
    elif net:
        rtype = "CSV"
        if args.output:
            rtype = args.output
        nglib.query.net.get_networks_on_cidr(args.search, rtype=rtype)
    elif ip:
        rtype = "TREE"
        if args.output:
            rtype = args.output
        nglib.query.net.get_net(args.search, rtype=rtype, days=args.days)
    elif text:
        rtype = "TREE"
        if args.output:
            rtype = args.output
        nglib.query.universal_text_search(args.search, args.vrange, rtype=rtype)
    else:
        print("Unknown Search:", args.search)

else:
    parser.print_help()
    print()
