#!/usr/bin/env python3
#
# Generate All VLANs on Switches with MGMT Group
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
configDir = "/scripts/sendjob/configs/"
#configDir = "/tftpboot/"

# Argument Parser
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(description='Generate VLAN Database')
parser.add_argument("-vl", metavar='vlans', help="Single Vlan or Vlan range to generate on (eg. 1-1005)", type=str)
parser.add_argument("-df", metavar='devicelist', help="Devicelist CSV file from NetDB", type=str)
parser.add_argument("-of", metavar='outfile', help="Output File for CSV", type=str)
parser.add_argument("-debug", help="Set debugging level", type=int)

# Argument Reference
args = parser.parse_args()

# Global Variables
vhigh = 0
vlow = 0
switches = []
vlans = []

DEBUG = 0
if args.debug: DEBUG = args.debug


# Get the High and Low VLAN Range variables
def process_vlans(vlanRange):
    global vhigh
    global vlow

    (vlow, vhigh) = get_vlan_range(vlanRange)

    if DEBUG: print("VLAN Range Low: " + str(vlow) + " High: " + str(vhigh), file=sys.stderr)

def get_vlan_range(vlan_range):
    vlans = vlan_range.rsplit("-")
    v_low  = int(vlans[0])

    if len(vlans) > 1:
        if int(vlans[1]) <= 4096:
            v_high = int(vlans[1])
        else:
            v_high = 4096
    else:
        v_high = v_low
    return(v_low, v_high)


# Load the config line by line in to config list
def loadConfig(switch):
    swfile = configDir + switch + "-confg"

    global location
    location = None
    cfg = []

    f = open(swfile)

    for line in f:
        cfg.append(line.rstrip())
        if re.search('snmp-server location',line):
            line = line.replace('"', '')
            line = line.replace("'", "")
            location = line.strip('snmp-server location ').rstrip()

    return cfg

# Load Devicelist.csv file looking for arp devicelist plus mgmtgroup
def loadDevicelist(devfile):
    if DEBUG: print("Loading Devicelist: " + devfile, file=sys.stderr)

    f = open(devfile, "r")
    for line in f:
        mgmt = None
        if re.search('\,(mgmtgroup)', line):
            mgmtre = re.search('mgmtgroup\=(\w+)', line)
            mgmt = mgmtre.group(1)
            line = line.rstrip()
            if DEBUG>1: print(line)
            dev = line.rsplit('.')
            switches.append(dev[0] + "," + mgmt)

# Write results to file
def saveCSV(data):

    save = open(args.of, "w")
    print("MGMT,VID,VName,Switch,STP", file=save)

    print(*sorted(data), sep='\n', file=save)
    save.close()


# Scan config for per int vlan information
def getVlans(config,switch,mgmtgroup):

    # Initial flow control variables
    vdb = dict()
    stp = dict()
    vlist = []
    inside = 0

    # Parse each line in config looking for interface VLAN
    for line in config:
        line = line.strip()

        # Preload searches with (grouping) of data to recall later
        vl           = re.search('^vlan (\d+)$', line)     #Standalone VLAN
        vrange       = re.search('^vlan (\d+\-\d+)', line) #VLAN Range (NXOS) (noname)
        vlist_match  = re.search('^vlan (\d+)(,\d+)+$',line) #VLAN List (noname)
        vname        = re.search('^name\s+(\w+\-*\w*\-*\w*\-*\w*)', line)
        peerstp      = re.search('^\s*vlan\s+(.*)root\spriority\s(\d+)', line)
        catstp       = re.search('^spanning-tree\svlan\s(.*)\spriority\s(\d+)', line)
        #descre = re.search('description', line)

        # Match on interface VLAN Line
        if vl:
            vdb['id']   = vl.group(1)

            # If interface is in Range, print and keep track of that
            if int(vdb['id']) >= vlow and int(vdb['id']) <= vhigh:
                #print("Found VLAN: " + vdb['id'])
                inside = 1

            # Outside Interface Vlan Range, save any data, mark outside
            else:
                inside = None
                vdb = dict()

        # VLAN Name
        elif vname and inside:
            vdb['name'] = vname.group(1)
            stpval = 0
            if vdb['id'] in stp.keys():
                stpval = stp[vdb['id']]
            mvlan = mgmtgroup + "-" + vdb['id']
            if DEBUG>1: print("Closing out VLAN {:} {:} on {:}".format(vdb['id'], vdb['name'], switch))
            vlist.append(mgmtgroup + "," + vdb['id'] + "," + vdb['name'] + "," + switch)
            vdb = dict()

        # Handle unnamed VLAN Ranges
        elif vrange:
            (v_low, v_high) = get_vlan_range(vrange.group(1))
            #print("Found NoName Range",switch,v_low,v_high)

            while v_low <= v_high:
                vlist.append(mgmtgroup + "," + str(v_low) + "," + "NONAME" + "," + switch)
                v_low = v_low+1


        # Handle unamed vlans as a list
        elif vlist_match:
            #print("Found NoName List",switch,vlist_match.group(1),vlist_match.group(2))
            vladd = vlist_match.group(1)+vlist_match.group(2)
            vla   = vladd.split(',')
            for v in vla:
                #print("Adding",switch,v)
                vlist.append(mgmtgroup + "," + v + "," + "NONAME" + "," + switch)

        elif peerstp:
            stp = getSTP(stp, peerstp.group(1), peerstp.group(2))
            #print(line)
        elif catstp:
            stp = getSTP(stp, catstp.group(1), catstp.group(2))
            #print(line)

        # Outside VLAN
        elif re.search('^(\w+|\!)', line):
            inside = 0
            vdb = dict()

    # Close out vlist and save to vlans
    for entry in vlist:
        (vmgmt,vid,vname,switch) = entry.split(',')
        stpval = 0
        if vid in stp.keys():
            stpval = stp[vid]
        saveVLAN(vmgmt,vid,vname,switch,stpval)

# Process STP Root Values
def getSTP(stp,vRange,priority):
    #print(vRange,priority)

    vr = vRange.split(',')

    for vlan in vr:
        if re.search('\-', vlan):
            (low,high) = vlan.split('-')
            #print("Range:",low,high,priority)
            for i in range(int(low),int(high)+1):
                #print(i,priority)
                stp[str(i)] = priority
        else:
            #print(vlan,priority)
            stp[vlan] = priority

    return stp


# Save vlan data to list
def saveVLAN(vlan,vid,vname,switch,stp):
    global vlans

    if DEBUG: print("Saving data: " + str(vlan) + "," + str(vid) + "," + str(vname) + "," + str(switch) + "," + str(stp))
    vlans.append(str(vlan) + "," + str(vid) + "," + str(vname) + "," + str(switch) + "," + str(stp))


## Process Arguments to generate output
# Got VLAN Range and Switch Name
if args.vl and args.df:
    process_vlans(args.vl)
    loadDevicelist(args.df)

    for switch in switches:
        sg = switch.split(',')

        config = list()
        try:
            config = loadConfig(sg[0])
        except:
            print("Warning: Could not load config for " + sg[0])

        if config:
            getVlans(config,sg[0],sg[1])

    if args.of:
        saveCSV(vlans)

# Print Help
else:
    parser.print_help()
    print()
