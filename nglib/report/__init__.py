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
"""Generates Reports on NetGrph Data"""

import csv
import re
import os
import sys
import logging
import functools
import configparser
import ipaddress
import nglib

verbose = 0
logger = logging.getLogger(__name__)


def get_vlan_report(vrange, report="all", rtype="TREE"):
    """Generate VLAN Reports"""

    rtypes = ('TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        # Full VLAN Report
        if report == "full":
            logger.info("Query: Generating Full VLAN Report (%s) for %s", vrange, nglib.user)

            # Get all VLANs as NGTree
            ngtree = get_vlan_data(vrange, rtype)
            if '_ccount' in ngtree.keys():
                nglib.query.exp_ngtree(ngtree, rtype)
            else:
                print("No Vlans in Range", vrange)

        # Empty VLAN Report
        elif report == "empty":
            logger.info("Query: Generating Empty VLAN Report (%s) for %s", vrange, nglib.user)

            # Get all VLANs as NGTree
            ngtree = get_vlan_data(vrange, rtype)

            # Found some VLANs in Range
            if '_ccount' in ngtree:
                etree = nglib.ngtree.get_ngtree("Empty VLAN Report", tree_type="VIDs")
                (clist, _) = get_children(ngtree)

                # Find Empty VLANs in NGTree
                for cv in clist:
                    get_empty_vlans(ngtree[cv], etree)

                # Found Empty VLANs, count and print
                if '_ccount' in etree.keys():
                    etree['Empty VLAN Count'] = etree['_ccount']
                    nglib.query.exp_ngtree(etree, rtype)
                    return etree
                else:
                    print("No Empty Vlans in Range", vrange)

            else:
                print("No Vlans in Range", vrange)
    else:
        raise Exception("RType Not Supported, use:" + str(rtypes))


def get_empty_vlans(ngtree, etree):
    """
    Find all empty VLANs on a VID tree instance

    Notes: Called recursively on any bridge trees and builds etree
    """

    (vidlist, _) = get_children(ngtree)

    # VID in Bridge Group
    for vid in vidlist:

        # No MACs in VLAN
        if 'MAC Count' not in ngtree[vid].keys():
            (childlist, ccount) = get_children(ngtree[vid])
            if not ccount:
                #nglib.ngtree.print_ngtree(ngtree[vid], dict())
                nglib.ngtree.add_child_ngtree(etree, ngtree[vid])
            else:
                get_empty_vlans(ngtree[vid], etree)

    return etree

def get_vlan_data(vrange, rtype):
    """Get all vlans in a range for reports"""

    allSwitches = True
    if rtype == "TREE":
        allSwitches = False

    (vlow, vhigh) = nglib.query.vlan.get_vlan_range(vrange)

    vlans = nglib.bolt_ses.run(
        'MATCH(v:VLAN) WHERE toInt(v.vid) >= {vlow} AND toInt(v.vid) <= {vhigh} '
        + 'RETURN DISTINCT v.vid AS vid ORDER BY toInt(vid)',
        {"vlow": vlow, "vhigh": vhigh})

    pngtree = nglib.ngtree.get_ngtree("Report", tree_type="VIDs")

    for v in vlans:
        vtree = nglib.query.vlan.search_vlan_id(v['vid'], allSwitches=allSwitches)
        nglib.ngtree.add_child_ngtree(pngtree, vtree)
    return pngtree


def get_dev_report(dev, rtype="NGTREE"):
    """
    Get all devices on a regex
    
    Note: Only returns devices in a mgmt group
    """    

    rtypes = ('TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:
        logger.info("Query: Generating Device Report (%s) for %s", dev, nglib.user)

        devices = nglib.bolt_ses.run(
            'MATCH(s:Switch) WHERE s.name =~ {dev} '
            + 'RETURN s.name AS name, s.mgmt AS mgmt ORDER BY name',
            {"dev": dev})

        ngtree = nglib.ngtree.get_ngtree("Report", tree_type="DEVs")
        ngtree['Device Regex'] = dev

        for d in devices:
            if d["mgmt"]:
                cngtree = nglib.query.dev.get_device(d["name"])
                if cngtree:
                    nglib.ngtree.add_child_ngtree(ngtree, cngtree)

        # Found Devices, count and print
        if '_ccount' in ngtree.keys():
            ngtree['Device Count'] = ngtree['_ccount']
            nglib.query.exp_ngtree(ngtree, rtype)
            return ngtree
        else:
            print("No Devices found on regex:", dev)

    else:
        raise Exception("RType Not Supported, use:" + str(rtypes))


def get_children(ngtree):
    """Return list of children and count in ngtree"""

    clist = []

    vcount = 1
    if '_ccount' not in ngtree.keys():
        return(clist, 0)
    else:
        while vcount <= int(ngtree['_ccount']):
            cname = "_child"
            if vcount < 10:
                cname += "00" + str(vcount)
            elif vcount < 100:
                cname += "0" + str(vcount)
            else:
                cname += str(vcount)
            clist.append(cname)
            vcount += 1
        return(clist, vcount)
