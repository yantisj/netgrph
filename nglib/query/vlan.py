#!/usr/bin/env python
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
"""
NetGrph VLAN Query Routines

"""
import sys
import os
import logging
import nglib
from nglib.query.nNode import getJSONProperties

logger = logging.getLogger(__name__)


def get_vlan_range(vlanRange):
    """Return the Low and High Values for a range"""

    vlans = vlanRange.rsplit("-")
    vlow = int(vlans[0])
    if len(vlans) > 1:
        if int(vlans[1]) > 4096:
            vhigh = 4096
        else:
            vhigh = int(vlans[1])
    else:
        vhigh = vlow

    if nglib.verbose > 2:
        print("VLAN Range Low: " + str(vlow) + " High: " + str(vhigh), file=sys.stderr)

    return vlow, vhigh


def search_vlan_id(vid, rtype="NGTREE", allSwitches=True):
    """Search a VLAN ID for all Bridge Groups"""

    rtypes = ('TREE', 'JSON', 'YAML', 'NGTREE')

    # Truncate Switches when Tree
    if rtype == "TREE":
        allSwitches = False

    if rtype in rtypes:

        if rtype != "NGTREE":
            logger.info("Query: VLAN ID %s for %s", vid, nglib.user)

        vnames = get_vlan_bridges(vid)

        # Attach trees to parent tree if count more than 1
        pngtree = nglib.ngtree.get_ngtree(str(vid), tree_type="VID")

        vcount = 0
        for vn in vnames.keys():
            vcount = vcount + 1

            # Truncate switches on tree returns
            if rtype == "TREE":
                ngtree = load_bridge_tree(vn, getSW=allSwitches)
                nglib.ngtree.add_child_ngtree(pngtree, ngtree)
            else:
                ngtree = load_bridge_tree(vn, getSW=allSwitches)
                nglib.ngtree.add_child_ngtree(pngtree, ngtree)

        # Export Results
        nglib.query.exp_ngtree(pngtree, rtype)
        return pngtree

    else:
        raise Exception("RType Not Supported, use:" + str(rtypes))


def get_vtree(vname, rtype="NGTREE"):
    """Get a VTree on a Vlan Name"""

    rtypes = ('TREE', 'JSON', 'YAML', 'NGTREE')

    # Truncate Switches when Tree
    allSwitches = True
    if rtype == "TREE":
        allSwitches = False

    if rtype in rtypes:

        ngtree = load_bridge_tree(vname, getSW=allSwitches)
        # Export Results
        nglib.query.exp_ngtree(ngtree, rtype)
        return ngtree

    else:
        raise Exception("RType Not Supported, use:" + str(rtypes))


def load_bridge_tree(vname, root=True, getSW=False):
    """
    Create a Bridge Tree in NetGrph Object Format
    Recursively Build Trees for child vnames
    Starts from the root device and builds out from there.

    Notes: getSW returns all switches instead of truncated (JSON/YAML)
    """

    sMax = 7
    if getSW:
        sMax = 10000

    # Initialize Empty Tree
    ngtree = nglib.ngtree.get_ngtree(vname, tree_type="VNAME")

    # Find VLAN
    vlan = get_vlan(vname)

    # Find Switches for VLAN
    swtree = get_sw_from_vlan(vname)

    if len(vlan) > 0:
        vrec = vlan.records[0]
        vname = vrec.vname
        scount = len(swtree)

        # Get NetDB Port and MAC Counts if they exist
        (pcount, mcount) = get_vlan_counts(vname)

        # Root Search
        vroot = None
        rootSearch = get_root_from_vlan(vname)
        if len(rootSearch) > 0:
            vroot = rootSearch.records[0].root

        # L3 Search FIXME (get dict)
        cidr = None
        vrf = None
        router = None
        gateway = None

        l3search = get_l3_from_l2(vname)
        if len(l3search) > 0:
            cidr = l3search.records[0].cidr
            vrf = l3search.records[0].vrf
            router = l3search.records[0].router
            gateway = l3search.records[0].gateway

        # Populate ngtree with variables
        if cidr:
            ngtree['CIDR'] = cidr
        if vrf:
            ngtree['VRF'] = vrf
        if router:
            ngtree['Router'] = router
        if gateway:
            ngtree['Gateway'] = gateway
        if vrec.lroot:
            ngtree['localroot'] = vrec.lroot
        if vrec.lstp:
            ngtree['localstp'] = vrec.lstp
        if root:
            ngtree['VLAN ID'] = vrec.vid
        ngtree['Description'] = vrec.desc
        if vroot:
            ngtree['Root'] = vroot
        ngtree['Switch Count'] = scount

        # NetDB Port and MAC Counts
        if pcount:
            ngtree['Port Count'] = pcount
        if mcount:
            ngtree['MAC Count'] = mcount

        # SW Tree Search for list and counts
        if len(swtree):
            slist = []
            scount = 0
            for sw in swtree:
                if scount < sMax:
                    slist.append(sw.name)
                if scount == sMax:
                    slist.append("...")
                scount = scount+1
            ngtree['Switches'] = slist


        # Only Find Parent for root vname searches
        if root:
            # Find Parent VLAN
            parent = get_parent_vlan(vname)
            if len(parent) > 0:
                pvname = parent.records[0].vname
                pngtree = get_parent_ngtree(pvname)
                nglib.ngtree.add_parent_ngtree(ngtree, pngtree)


        # Find Child VLANs
        children = get_child_vlans(vname)
        if len(children) > 0:
            for c in children:
                cvname = c.vname
                cngtree = load_bridge_tree(cvname, root=False, getSW=getSW)
                cngtree = add_bridge_data(cngtree, vname, cvname)
                if cngtree:
                    nglib.ngtree.add_child_ngtree(ngtree, cngtree)

    else:
        raise Exception("No VLAN Found (expecting VNAME eg. Core-16): " + vname)

    return ngtree


def get_parent_ngtree(vname):
    """
    Build a Parent NGTree (only one Parent allowed)
    FixME (Recursively)
    """
    vlan = get_vlan(vname)

    ngtree = nglib.ngtree.get_ngtree(vname, tree_type="Parent")

    if len(vlan) > 0:
        vrec = vlan.records[0]

        # L2 Search
        vroot = None
        rootSearch = get_root_from_vlan(vname)
        if len(rootSearch) > 0:
            vroot = rootSearch.records[0].root

        # L3 Search
        cidr = None
        vrf = None
        router = None
        gateway = None

        l3search = get_l3_from_l2(vname)
        if len(l3search) > 0:
            cidr = l3search.records[0].cidr
            vrf = l3search.records[0].vrf
            router = l3search.records[0].router
            gateway = l3search.records[0].gateway

        # Populate ngtree with variables
        if cidr:
            ngtree['CIDR'] = cidr
        if gateway:
            ngtree['Gateway'] = gateway
        if vrf:
            ngtree['VRF'] = vrf
        if router:
            ngtree['Router'] = router
        ngtree['localroot'] = vrec.lroot
        ngtree['localstp'] = vrec.lstp
        ngtree['VLAN ID'] = vrec.vid
        ngtree['Description'] = vrec.desc
        ngtree['Root'] = vroot

    return ngtree


def get_vlan_bridges(vid):
    """
    Get all distinct vlan bridges returning the root node of the tree for each
    Used for VLAN ID Searches
    """

    vfound = dict()
    vname = dict()
    vid = str(vid)

    vnames = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {vid:{vid}}) RETURN v.name AS name, v.vid AS vid',
        vid=vid)


    # Found VID
    if len(vnames) > 0:
        for vn in vnames.records:
            if nglib.verbose:
                print("Found", vn.name, vn.vid)

            if vn.name not in vfound.keys():

                # Mark VName as found
                vfound[vn.name] = 1

                vbridges = nglib.py2neo_ses.cypher.execute(
                    'MATCH (v:VLAN {name:{vname}})-[:BRIDGE*]-(rv:VLAN) RETURN rv.name AS rname',
                    vname=vn.name)

                # Standalone VLAN
                if len(vbridges) == 0:
                    if nglib.verbose:
                        print(vid, "not bridged on", vn.name)
                    vname[vn.name] = vid

                # Search Bridge remote for root node
                else:
                    rFound = False
                    for rvn in vbridges:
                        if nglib.verbose:
                            print("Found RV", rvn.rname)

                        # Mark all members of bridge as found
                        vfound[rvn.rname] = 1

                        findroot = nglib.py2neo_ses.cypher.execute(
                            'MATCH (v:VLAN {name:{vname}})<-[:BRIDGE]-(rv:VLAN) '
                            + 'RETURN rv.name AS rname',
                            vname=rvn.rname)

                        # Root node has no outgoing BRIDGE relationships
                        if len(findroot) == 0:
                            if nglib.verbose:
                                print("Found root", rvn.rname)
                            vname[rvn.rname] = vid
                            rFound = True

                    # I must be the root node since others have bridge relationships
                    if not rFound:
                        if nglib.verbose:
                            print("I'm the root of", vn.name)
                        vname[vn.name] = vid

    else:
        raise Exception("No VID Found (expecting VLAN id in range 1-4096): " + vid)

    return vname


def get_vlans_on_group(group, vrange):
    """Get all VLANs in a Management group"""

    logger.info("Query: VLAN DB %s for %s", group, nglib.user)

    (vlow, vhigh) = nglib.query.vlan.get_vlan_range(vrange)

    vlist = []

    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {mgmt:{group}}) RETURN v',
        group=group)

    if len(results) > 0:
        for v in results:
            vlan = v.v
            vp = getJSONProperties(vlan)
            vp['root'] = "None"

            # Get NetDB MAC and Port Counts if they Exist
            (pcount, mcount) = get_vlan_counts(vp['name'])
            vp['pcount'] = pcount
            vp['mcount'] = mcount

            if 'desc' not in vp.keys():
                vp['desc'] = 'None'

            if vlow <= int(vp['vid']) <= vhigh:
                switches = nglib.py2neo_ses.cypher.execute(
                    'MATCH (s)<-[e:Switched]-(v:VLAN {name:{name}}) RETURN s.name as name',
                    name=vp['name'])

                root = nglib.py2neo_ses.cypher.execute(
                    'MATCH (s)<-[e:Switched]-(v:VLAN {name:{name}}) '
                    + 'OPTIONAL MATCH (v)-[b:BRIDGE*]-(rv)-[r:ROOT]->(rs) '
                    + 'OPTIONAL MATCH (v)-[:ROOT]-(lr) '
                    + 'RETURN s.name as name, rs.name as root, lr.name as lroot',
                    name=vp['name'])

                # Remote Root Tree Discovery
                if len(root) > 0:
                    vp['root'] = root.records[0].root

                    # Local root if no remote root
                    if root.records[0].lroot:
                        vp['root'] = root.records[0].lroot

                if len(switches):
                    scount = 0
                    slist = []
                    for s in switches.records:
                        scount = scount + 1
                        if s.name != vp['root']:
                            slist.append(s.name)
                    vp['switches'] = slist
                    vp['scount'] = scount

                vlist.append(vp)

        vtotal = len(vlist)
        sortedList = sorted(vlist, key=lambda k: int(k['vid']))
        print("Total: " + str(vtotal))
        print()
        print(" VID             Name           Sw/Macs/Ports  Root       Switches")

        # Header Size
        try:
            tsize = os.get_terminal_size()
            tsize = tsize.columns
        except OSError:
            tsize = 80
        print("-" * tsize)

        for en in sortedList:

            slen = tsize - 65

            swl = ''
            for sw in en['switches']:
                swl = swl + " " + sw
            swlt = (swl[:slen] + '..') if len(swl) > slen else swl

            counts = "{:3>}/{:4>}/{:<4}".format(
                str(en['scount']), str(en['mcount']), str(en['pcount']))

            print("{:>4} : {:<25}  {:<12} {:<9} {:}".format(
                en['vid'], en['desc'], counts,
                str(en['root']), swlt))

        print()

    else:
        print("No VLANs for for Management Group: " + group)
        nglib.query.display_mgmt_groups()

def add_bridge_data(ngtree, parent, child):
    """Add data to ngtree about a parent bridge"""

    bridge = nglib.bolt_ses.run(
        'MATCH (pv:VLAN {name:{pvname}})-[e:BRIDGE]->(cv:VLAN {name:{cvname}}) '
        + 'RETURN e.pswitch AS pswitch, e.cswitch AS cswitch',
        {"pvname":parent, "cvname":child})
    
    for rec in bridge:
        ngtree["Bridge"] = rec["cswitch"] + ' <-> ' + rec["pswitch"]

    return ngtree


def get_l3_from_l2(vname):
    """Get L3 Network from L2 VLAN"""

    l3 = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {name:{vname}})<-[sw:L3toL2]-(n:Network)-[e:ROUTED_BY|ROUTED]->(r:Router)'
        + 'return n.cidr AS cidr, n.gateway AS gateway, n.vrf AS vrf, r.name as router',
        vname=vname)

    return l3

def get_sw_from_vlan(vname):
    """Get all switches connected to a VLAN"""

    swtree = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {name:{vname}})-[sw:Switched]->(s:Switch)'
        + 'return s.name AS name,sw',
        vname=vname)

    return swtree

def get_root_from_vlan(vname):
    """Find the VLAN Root from a VNAME"""

    root = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {name:{vname}})-[sw:ROOT]->(s:Switch) return s.name AS root',
        vname=vname)

    return root


def get_vlan(vname):
    """Get a VNAME"""

    vlan = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {name:{vname}})'
        + 'return v.name as vname, v.lstp AS lstp, v.lroot AS lroot, v.vid AS vid, v.desc AS desc',
        vname=vname)

    return vlan

def get_vlan_counts(vname):
    """Returns port and mac counts for a vlan from NetDB"""

    counts = nglib.bolt_ses.run(
        'match(v:VLAN {name:{vname}})-[e:Switched]->(s:Switch) '
        + 'RETURN SUM(e.pcount) AS pcount, SUM(e.mcount) AS mcount',
        {"vname": vname})

    for en in counts:
        return(en['pcount'], en['mcount'])

    return(0, 0)

def get_parent_vlan(vname):
    """Find the Parent VLAN from here"""

    parent = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {name:{vname}})<-[sw:BRIDGE]-(pv:VLAN) RETURN pv.name AS vname',
        vname=vname)

    return parent

def get_child_vlans(vname):
    """Find all child vlans on a VNAME"""

    children = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {name:{vname}})-[sw:BRIDGE]->(cv:VLAN) RETURN cv.name AS vname',
        vname=vname)

    return children
