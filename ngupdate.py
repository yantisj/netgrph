#!/usr/bin/env python3
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
"""
 NetGrph Update Routines
 - Imports Various Network Data from CSV into Neo4j
 - Helper functions for database maintenance
"""
import re
import os
import argparse
import configparser
import logging
import getpass
from timeit import default_timer as timer
import nglib
import nglib.dev_update
import nglib.net_update
import nglib.fw_update
import nglib.cache_update
import nglib.vlan_update
import nglib.alerts


# Default Config File Location
config_file = '/etc/netgrph.ini'
alt_config = './docs/netgrph.ini'

#print("Config:",config_file,dirname)

parser = argparse.ArgumentParser()

parser = argparse.ArgumentParser(description='Manage the NetGraph Database')
parser.add_argument("-full", help="Full Update on the Database",
                    action="store_true")
parser.add_argument("-id", help="Import Devicelist into DB",
                    action="store_true")
parser.add_argument("-ind", help="Import Neighbor into DB",
                    action="store_true")
parser.add_argument("-ild", help="Import Links Data into DB",
                    action="store_true")
parser.add_argument("-ivrf", help="Import VRF,Seczone Data",
                    action="store_true")
parser.add_argument("-inet", help="Import Allnets Network Data",
                    action="store_true")
parser.add_argument("-ivlan", help="Import All VLANs Network Data",
                    action="store_true")
parser.add_argument("-uvlan", help="Update VLAN Names and Bridges",
                    action="store_true")
parser.add_argument("--ignoreNew", help="Do Not Create NewNetwork Events on Load",
                    action="store_true")
parser.add_argument("-isnet", help="Import Supernets Network Data",
                    action="store_true")
parser.add_argument("-ifw", help="Import FW Data from CSV file",
                    action="store_true")
parser.add_argument("-ifile", metavar='file',
                    help="Import Cypher Statements Directly (CREATE|MERGE|MATCH)",
                    type=str)
parser.add_argument("-unetdb", help="Update Data from NetDB (optional)",
                    action="store_true")
parser.add_argument("--adduser", metavar="user", help="Add API User to DB", type=str)
parser.add_argument("--newpass", metavar="user", help="Update Password", type=str)
parser.add_argument("--testuser", metavar="user", help="Test Authentication", type=str)
parser.add_argument("--deluser", metavar="user", help="Delete API User", type=str)
parser.add_argument("--alerts", help="Process Alerts", action="store_true")
parser.add_argument("--clearEdges", help="Clear Edges Older than -h hours",
                    action="store_true")
parser.add_argument("--clearNodes", help="Clear Nodes Older than -h hours",
                    action="store_true")
parser.add_argument("--reSeed", help="Reseed All Neighbors (takes a few iterations)",
                    action="store_true")
parser.add_argument("--dropDatabase",
                    help="Clear all database Data (Warning: drops all data)",
                    action="store_true")
parser.add_argument("--hours", metavar='hours', help="Hours in Past",
                    type=float)
parser.add_argument("--conf", metavar='file', help="Alternate Config File",
                    type=str)
parser.add_argument("--debug", help="Set debugging level", type=int)
parser.add_argument("-v", help="Verbose Output", action="store_true")

args = parser.parse_args()

# Alternate Config File
if args.conf:
    config_file = args.conf

if 'NG_config_file' in os.environ:
    config_file = os.environ['NG_config_file']

# Test configuration exists
if not os.path.exists(config_file):
    if not os.path.exists(alt_config):
        raise Exception("Configuration File not found", config_file)
    else:
        config_file = alt_config

config = configparser.ConfigParser()
config.read(config_file)
config = nglib.override_config(config)

verbose = 0
if args.v:
    verbose = 1
if args.debug:
    verbose = args.debug

# Setup Globals Debugging
nglib.verbose = verbose

# Initialize Library
nglib.init_nglib(config_file)
logger = logging.getLogger("updatengdb")

ngfiles = config['ngfiles']

def run_cmd(func, fileName=None, devFile=None):
    """
    Run a function and optionally time it

    FIXME: Refactor to accept *args
    """

    l_start = timer()

    if devFile:
        func(fileName, devFile)

    elif fileName:
        func(fileName)
    else:
        func()

    l_stop = timer()
    l_runtime = "%.3f" % (l_stop - l_start)
    if verbose:
        logger.info("|---> Time: " + l_runtime + "sec")


# Full Import Requested
if args.full:

    logger.info("Full Import Requested")
    start = timer()
    run_cmd(nglib.dev_update.import_vrfs, fileName=ngfiles['vrfs'])
    run_cmd(nglib.dev_update.import_devicelist,
            fileName=ngfiles['devices'], devFile=ngfiles['device_info'])
    run_cmd(nglib.dev_update.import_neighbors, fileName=ngfiles['neighbors'])
    run_cmd(nglib.net_update.import_networks, fileName=ngfiles['networks'])
    run_cmd(nglib.net_update.import_supernets, fileName=ngfiles['supernets'])
    run_cmd(nglib.fw_update.import_fw, fileName=ngfiles['firewalls'])

    run_cmd(nglib.vlan_update.import_vlans, fileName=ngfiles['vlans'])
    run_cmd(nglib.vlan_update.import_links, fileName=ngfiles['links'])

    run_cmd(nglib.vlan_update.update_vlans)
    stop = timer()
    runtime = "%.3f" % (stop - start)
    logger.info("Import Completed in " + str(runtime) + "sec")

# Reseed is a single operation
elif args.reSeed:
    nglib.dev_update.reseed_neighbors()

# Drop everything in the database
elif args.dropDatabase:
    nglib.drop_database()

# Alerts
elif args.alerts:
    nglib.alerts.gen_new_network_alerts()
    nglib.alerts.gen_new_vlan_alerts()


# NetDB
elif args.unetdb:
    nglib.vlan_update.netdb_vlan_import()
elif args.id:
    nglib.dev_update.import_devicelist(ngfiles['devices'],
                                       ngfiles['device_info'])
elif args.ind:
    nglib.dev_update.import_neighbors(ngfiles['neighbors'])
elif args.ild:
    nglib.vlan_update.import_links(ngfiles['links'])
elif args.ivrf:
    nglib.dev_update.import_vrfs(ngfiles['vrfs'])
elif args.inet:
    nglib.net_update.import_networks(ngfiles['networks'], ignore_new=args.ignoreNew)
elif args.ivlan:
    nglib.vlan_update.import_vlans(
        fileName=ngfiles['vlans'], ignore_new=args.ignoreNew)
elif args.uvlan:
    nglib.vlan_update.update_vlans()
elif args.isnet:
    nglib.net_update.import_supernets(ngfiles['supernets'])
elif args.ifile:
    nglib.import_cypher(args.ifile)
elif args.ifw:
    nglib.fw_update.import_fw(ngfiles['firewalls'])

# Clear Edges and Nodes
elif args.clearEdges and args.hours:
    nglib.cache_update.clear_edges(args.hours)
elif args.clearNodes and args.hours:
    nglib.cache_update.clear_nodes(args.hours)

# Must need help
else:
    parser.print_help()
