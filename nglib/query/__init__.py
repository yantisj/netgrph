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
"""NetGrph Queries Library (Parent Module)"""

import csv
import re
import os
import sys
import logging
import functools
import configparser
import ipaddress
import nglib
import nglib.ngtree
import nglib.query.vlan
import nglib.query.dev
import nglib.query.net
import nglib.query.nNode
import nglib.query.path


logger = logging.getLogger(__name__)

def exp_ngtree(ngtree, rtype):
    """Prints or Returns NGTree in Requested format"""

    if rtype == "TREE":
        nglib.ngtree.print_ngtree(ngtree, dtree=dict())
    elif rtype == 'QTREE':
        nglib.ngtree.export.exp_qtree(ngtree)
    elif rtype == "CSV":
        nglib.ngtree.export.exp_CSV(ngtree)
    elif rtype == "JSON":
        nglib.ngtree.export.exp_JSON(ngtree)
    elif rtype == "YAML":
        nglib.ngtree.export.exp_YAML(ngtree)
    else:
        return ngtree

def display_mgmt_groups():
    """Print all Management Groups to the Screen"""

    mgmt = nglib.py2neo_ses.cypher.execute(
        'MATCH (s:Switch) RETURN DISTINCT(s.mgmt) as name ORDER BY name')

    if len(mgmt) > 0:
        print("Available Groups:")
        for s in mgmt.records:
            print("> " + str(s.name))
    else:
        print("No management groups found in DB")


def print_dict_csv(netList):
    """Print out List of Dictionary Objects as CSV"""

    netKeys = []

    # Get Dict keys for CSV Out
    for key in sorted(netList[0].keys()):
        if key != "__values__":
            netKeys.append(key)

    netWriter = csv.writer(sys.stdout)
    netWriter.writerow(netKeys)

    # Go through all entries and dump them to CSV
    for en in netList:
        netValues = []
        for key in sorted(en.keys()):
            if key != "__values__":
                netValues.append(en[key])
        # Write Values to CSV
        netWriter.writerow(netValues)


def get_net_filter(group):
    """Try to get a filter from the config"""

    try:
        gFilter = nglib.config['NetAlertFilter'][group]
        return gFilter
    except:
        raise Exception("No Group Filter Found", group)


def check_net_filter(netDict, group=None, nFilter=None):
    """
    Filters Networks based on vrf:role (from supernets)

    Pass in a group filter to read from config, or a custom nFilter

    Examples:
    nst = all (all networks)

    # default VRF only with null supernet or new access layer supernets 10.177
    radonc = default:none|access-private|access-wan

    # EST wants all access layer networks plus all PCI networks
    est = default:none|access-private|access-wan pci:all

    # JCI Wants all fwutil networks
    jci = fwutil:all

    # COM wants only printer networks
    com = default:printer
    """

    if group:
        vDict = get_filter_dict(group=group)
    elif nFilter:
        vDict = get_filter_dict(nFilter=nFilter)

    # Check filter against vDict
    for vrf in vDict.keys():
        if netDict['VRF'] == vrf or vrf == "all":
            #print("VRF MATCH", vrf, netDict['VRF'])
            for role in vDict[vrf]:
                if netDict['NetRole'] == role or role == "all":
                    logger.debug("VRF and Role MATCH: %s, %s, %s, %s, %s",
                                 group, vrf, netDict['VRF'], netDict['NetRole'], netDict['CIDR'])
                    return True

                # No supernet role associated (none=None)
                elif role == "none" and not netDict['NetRole']:
                    logger.debug("VRF and Role MATCH on Null Role: %s, %s, %s, %s, %s",
                                 group, vrf, netDict['VRF'], netDict['NetRole'], netDict['CIDR'])
                    return True

                # No Match
                else:
                    logger.debug("NOMATCH VRF and Role: %s, %s, %s, %s, %s",
                                 group, vrf, netDict['VRF'], netDict['NetRole'], netDict['CIDR'])

    logger.debug("No Network Match for %s on %s", netDict['CIDR'], group)
    return False


@functools.lru_cache(maxsize=1)
def get_filter_dict(group=None, nFilter=None):
    """Process config for group or custom filter and cache it for each call"""

    vDict = dict()
    gFilter = None

    if group:
        gFilter = nglib.config['NetAlertFilter'][group]
    elif nFilter:
        gFilter = nFilter
    else:
        raise Exception("Must pass in group or filter")

    # Split all VRFs by spaces
    vrfFilters = gFilter.rsplit()

    # Process Filters
    for f in vrfFilters:

        # Multiple roles specified
        if re.search(':', f):
            (vrf, roles) = f.split(':')
            vDict[vrf] = []                   # Empty vDict List
            if re.search('|', roles):
                rList = roles.split('|')      # Split up multiple roles if exists
                for r in rList:
                    vDict[vrf].append(r)      # Append multiple roles to List
            else:
                vDict[vrf].append(roles)      # Append single role to list

        # All roles for VRF
        else:
            vDict[f] = []
            vDict[f].append("all")

    if nglib.verbose > 1:
        print("vDict Contents", str(vDict))

    return vDict

def universal_text_search(text, vrange, rtype="TREE"):
    """
    Try to find what someone is looking for based on a text string
    Uses a lot of try/except code, best to debug non-universal before
    debugging here.
    """

    if nglib.verbose:
        print("Universal Search for", text)

    found = False

    #Look for group filter first
    try:
        get_net_filter(text)
        nglib.query.net.get_networks_on_filter(text, rtype=rtype)
        found = True
    except:
        pass

    if not found:

        # Look for MGMT Group
        mgmt = nglib.bolt_ses.run(
            'MATCH (s:Switch {mgmt:{mgmt}}) RETURN DISTINCT(s.mgmt) as name',
            {"mgmt": text})

        for m in mgmt:
            nglib.query.vlan.get_vlans_on_group(text, vrange)
            found = True

    if not found:
        # Look for Device Name
        devices = nglib.bolt_ses.run(
            'MATCH (s:Switch {name:{switch}}) RETURN s.name as name',
            {"switch": text})

        for d in devices:
            nglib.query.dev.get_device(text, rtype=rtype, vrange=vrange)
            found = True

    if not found:
        print("Nothing found for Universal Search", text)
