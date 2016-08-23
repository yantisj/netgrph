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
Network Path Algorithms Between Switches and Routers

"""
import re
import sys
import logging
import subprocess
import nglib
import nglib.query.nNode
import nglib.netdb.ip

logger = logging.getLogger(__name__)


def get_full_path(src, dst, popt, rtype="NGTREE"):
    """ Gets the full path (switch->rt->VRF->rt->switch)

        Required NetDB for switchpath
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', 'NGTREE', 'QTREE')

    if rtype in rtypes:

        if 'onepath' not in popt:
            popt['onepath'] = True
        if 'l2path' not in popt:
            popt['l2path'] = True
        if 'verbose' not in popt:
            popt['verbose'] = False
        if nglib.verbose:
            popt['verbose'] = True

        logger.info("Query: Finding Full Path (%s --> %s) for %s",
                    src, dst, nglib.user)

        net1, net2 = src, dst
        n1tree, n2tree = None, None

        # Translate IPs to CIDRs
        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net1):
            n1tree = nglib.query.net.get_net(net1, rtype="NGTREE", verbose=popt['verbose'])
            if n1tree:
                net1 = n1tree['_child001']['Name']

        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net2):
            n2tree = nglib.query.net.get_net(net2, rtype="NGTREE", verbose=popt['verbose'])
            if n2tree:
                net2 = n2tree['_child001']['Name']

        srctree, dsttree, srcswp, dstswp = None, None, None, None

        if 'vrfcidr' not in n1tree['_child001']:
            print("Warning: Could not locate", src, file=sys.stderr)
            return
        if 'vrfcidr' not in n2tree['_child001']:
            print("Warning: Could not locate", dst, file=sys.stderr)
            return          

        # Routing Check
        routing = True
        if n1tree['_child001']['vrfcidr'] == n2tree['_child001']['vrfcidr']:
            routing = False

        if nglib.use_netdb:
            srctree = nglib.netdb.ip.get_netdb_ip(src)
            dsttree = nglib.netdb.ip.get_netdb_ip(dst)

        # Find Switched Path from Source to Router
        if srctree:
            router = n1tree['_child001']['Router']
            if 'StandbyRouter' in n1tree['_child001']:
                router = router + '|' + n1tree['_child001']['StandbyRouter']
            if 'Switch' in srctree and srctree['Switch']:
                srcswp = get_switched_path(srctree['Switch'], router, popt)
            else:
                srctree = None
                print("Warning: Could not find source switch data in NetDB:", src, file=sys.stderr)

        # Find Switched Path from Router to Destination
        if dsttree:
            router = n2tree['_child001']['Router']
            if 'StandbyRouter' in n2tree['_child001']:
                router = router + '|' + n2tree['_child001']['StandbyRouter']
            if 'Switch' in dsttree and dsttree['Switch']:
                dstswp = get_switched_path(router, dsttree['Switch'], popt)
            else:
                dsttree = None
                print("Warning: Could not find destination switch data in NetDB", \
                    dst, file=sys.stderr)

            # If only switching, update srcswp to show switched path
            if not routing and srctree and dsttree:
                srcswp = get_switched_path(srctree['Switch'], dsttree['Switch'], popt)

        # Same switch/vlan check
        switching = True
        if srctree and dsttree:
            if srctree['Switch'] == dsttree['Switch'] and \
                srctree['VLAN'] == dsttree['VLAN']:
                switching = False

        ## Create Parent Data Structure
        ngtree = nglib.ngtree.get_ngtree("L2-L4", tree_type="PATHs")

        # Populate Overall Paths
        if n1tree['_child001']['Name'] != n2tree['_child001']['Name']:
            ngtree["L3 Path"] = net1 + " -> " + net2
            ngtree["Lx Path"] = src + " -> " + dst
        if srctree and dsttree:
            ngtree["L2 Path"] = srctree['Switch'] + " (" + srctree['SwitchPort'] \
            + ") -> " + dsttree['Switch'] + " (" + dsttree['SwitchPort'] + ")"
        if popt['onepath']:
            ngtree["Traversal Type"] = 'Single Path'
        else:
            ngtree["Traversal Type"] = 'All Paths'

        ## Add the SRC Data
        if '_child002' in n1tree:
            n1tree['_child002']['_type'] = "SRC"
            if 'SwitchPort' in n1tree['_child002']:
                n1tree['_child002']['Name'] = src + ' ' + n1tree['_child002']['MAC'] \
                    + ' ' + str(n1tree['_child002']['Switch']) + '(' \
                    + str(n1tree['_child002']['SwitchPort']) \
                    + ') [vid:' + str(n1tree['_child002']['VLAN']) + ']'
            nglib.ngtree.add_child_ngtree(ngtree, n1tree['_child002'])

        # Add L2 path if not switching
        if not switching and '_child002' in n2tree:
            nglib.ngtree.add_child_ngtree(n1tree, n2tree['_child002'])
            n1tree['_type'] = "L2PATH"
            n1tree['Name'] = src + ' -> ' + dst

        # If there's src switched data add it
        if switching and srcswp:
            nglib.ngtree.add_child_ngtree(ngtree, srcswp)

        # Add L3 Gateway
        if switching and routing:
            n1tree['_child001']['_type'] = "L3GW"
            n1tree['_child001']['Name'] = n1tree['_child001']['Name'] \
                + ' ' + n1tree['_child001']['Router']
            if 'StandbyRouter' in n1tree['_child001']:
                n1tree['_child001']['Name'] = n1tree['_child001']['Name'] \
                    + '|' + n1tree['_child001']['StandbyRouter']
            nglib.ngtree.add_child_ngtree(ngtree, n1tree['_child001'])

        ## Check for routed paths (inter/intra VRF)
        rtree = get_full_routed_path(src, dst, popt)
        if rtree and 'PATH' in rtree['_type']:

            # Breakdown L4 Path
            if rtree['_type'] == 'L4-PATH':
                ngtree['L4 Path'] = rtree['Name']
                for p in sorted(rtree.keys()):
                    if '_child' in p:
                        nglib.ngtree.add_child_ngtree(ngtree, rtree[p])
            else:
                ngtree['L4 Path'] = 'VRF:' + n1tree['_child001']['VRF']
                nglib.ngtree.add_child_ngtree(ngtree, rtree)


        # Add the DST L3GW Data
        if switching and routing:
            n2tree['_child001']['_type'] = "L3GW"
            n2tree['_child001']['Name'] = n2tree['_child001']['Name'] \
                + ' ' + n2tree['_child001']['Router']
            if 'StandbyRouter' in n2tree['_child001']:
                n2tree['_child001']['Name'] = n2tree['_child001']['Name'] \
                    + '|' + n2tree['_child001']['StandbyRouter']
            nglib.ngtree.add_child_ngtree(ngtree, n2tree['_child001'])

        # Destination Switch Data
        if switching and dstswp:
            nglib.ngtree.add_child_ngtree(ngtree, dstswp)

        # NetDB Destination Data
        if '_child002' in n2tree:
            n2tree['_child002']['_type'] = "DST"
            if 'SwitchPort' in n2tree['_child002']:
                n2tree['_child002']['Name'] = dst + ' ' + n2tree['_child002']['MAC'] \
                    + ' ' + str(n2tree['_child002']['Switch']) + '(' \
                    + str(n2tree['_child002']['SwitchPort']) \
                    + ') [vid:' + str(n2tree['_child002']['VLAN']) + ']'
            nglib.ngtree.add_child_ngtree(ngtree, n2tree['_child002'])

        # Export NGTree
        ngtree = nglib.query.exp_ngtree(ngtree, rtype)
        return ngtree

def get_full_routed_path(src, dst, popt, rtype="NGTREE"):
    """ Gets the full L3 Path between src -> dst IPs including inter-vrf routing
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        if 'l2path' not in popt:
            popt['l2path'] = False
        if 'onepath' not in popt:
            popt['onepath'] = True
        if 'VRF' not in popt:
            popt['VRF'] = "default"

        srct, dstt, ngtree = None, None, None

        # Translate IPs to CIDRs
        if re.search(r'^\d+\.\d+\.\d+\.\d+$', src):
            srct = nglib.query.net.get_net(src, rtype="NGTREE", verbose=popt['verbose'])

        if re.search(r'^\d+\.\d+\.\d+\.\d+$', dst):
            dstt = nglib.query.net.get_net(dst, rtype="NGTREE", verbose=popt['verbose'])

        # Intra VRF
        if srct['_child001']['VRF'] == dstt['_child001']['VRF']:
            ngtree = get_routed_path(src, dst, popt)

        # Inter VRF
        else:
            secpath = get_fw_path(src, dst, popt, rtype="NGTREE")
            if secpath:
                ngtree = nglib.ngtree.get_ngtree(secpath['Name'], tree_type="L4-PATH")

                # Filter security path for relavent nodes
                first = True
                last = None
                for key in sorted(secpath.keys()):
                    if '_child' in key:
                        if re.search(r'(L4GW|L4FW)', secpath[key]['_type']):

                            # First Entry gets a route check
                            if first:
                                npopt = popt.copy()
                                npopt['VRF'] = srct['_child001']['VRF']
                                rtree = get_routed_path(src, secpath[key]['gateway'], popt)
                                if rtree:
                                    nglib.ngtree.add_child_ngtree(ngtree, rtree)
                                first = False
                            nglib.ngtree.add_child_ngtree(ngtree, secpath[key])
                            last = key

                # Last entry gets a route check
                if last:
                    npopt = popt.copy()
                    npopt['VRF'] = srct['_child001']['VRF']
                    rtree = get_routed_path(secpath[last]['gateway'], dst, popt)
                    if rtree:
                        nglib.ngtree.add_child_ngtree(ngtree, rtree)
        
        return ngtree


def get_routed_path(net1, net2, popt, rtype="NGTREE"):
    """
    Find the routed path between two CIDRs and return all interfaces and
    devices between the two. This query need optimization.

    - net1 and net2 can be IPs, and it will find the CIDR
    - Uses Neo4j All Shortest Paths on ROUTED Relationships
    - Returns all distinct links along shortest paths along with distance

    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        if 'l2path' not in popt:
            popt['l2path'] = False
        if 'onepath' not in popt:
            popt['onepath'] = True
        if 'VRF' not in popt:
            popt['VRF'] = "default"
        if 'verbose' not in popt:
            popt['verbose'] = True

        if popt['verbose']:
            logger.info("Query: Finding Routed Paths (%s --> %s) for %s",
                        net1, net2, nglib.user)

        hopSet = set()

        # Translate IPs to CIDRs
        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net1):
            n1tree = nglib.query.net.get_net(net1, rtype="NGTREE", verbose=popt['verbose'])
            net1 = n1tree['_child001']['Name']

        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net2):
            n2tree = nglib.query.net.get_net(net2, rtype="NGTREE", verbose=popt['verbose'])
            if n2tree:
                net2 = n2tree['_child001']['Name']

        ngtree = nglib.ngtree.get_ngtree("Path", tree_type="L3-PATH")
        ngtree["Path"] = net1 + " -> " + net2
        ngtree['Name'] = ngtree['Path']

        pathList = []
        pathRec = []

        # Finds all paths, then finds the relationships
        # rtrp = nglib.py2neo_ses.cypher.execute(
        #     'MATCH (sn:Network), (dn:Network), rp = allShortestPaths '
        #     + '((sn)-[:ROUTED|ROUTED_BY|ROUTED_STANDBY*0..12]-(dn)) '
        #     + 'WHERE ALL(v IN rels(rp) WHERE v.vrf = {vrf}) '
        #     + 'AND sn.cidr =~ {net1} AND dn.cidr =~ {net2}'
        #     + 'UNWIND nodes(rp) as r1 UNWIND nodes(rp) as r2 '
        #     + 'MATCH (r1)<-[l1:ROUTED]-(n:Network {vrf:{vrf}})-[l2:ROUTED]->(r2) '
        #     + 'OPTIONAL MATCH (n)-[:L3toL2]->(v:VLAN) '
        #     + 'RETURN DISTINCT r1.name AS r1name, l1.gateway AS r1ip, '
        #     + 'r2.name AS r2name, l2.gateway as r2ip, v.vid AS vid, '
        #     + 'LENGTH(shortestPath((sn)<-[:ROUTED|ROUTED_BY|ROUTED_STANDBY*0..12]->(r1))) '
        #     + 'AS distance ORDER BY distance',
        #     {"net1": net1, "net2": net2, "vrf": vrf})
        # Finds all paths, then finds the relationships
        rtrp = nglib.py2neo_ses.cypher.execute(
            'MATCH (sn:Network)-[:ROUTED_BY|ROUTED_STANDBY]-(sr), '
            + '(dn:Network)-[:ROUTED_BY|ROUTED_STANDBY]-(dr), rp = allShortestPaths '
            + '((sr)-[:ROUTED*0..12]-(dr)) '
            + 'WHERE ALL(v IN rels(rp) WHERE v.vrf = {vrf}) '
            + 'AND sn.cidr =~ {net1} AND dn.cidr =~ {net2}'
            + 'UNWIND nodes(rp) as r1 UNWIND nodes(rp) as r2 '
            + 'MATCH (r1)<-[l1:ROUTED]-(n:Network {vrf:{vrf}})-[l2:ROUTED]->(r2) '
            + 'OPTIONAL MATCH (n)-[:L3toL2]->(v:VLAN) '
            + 'RETURN DISTINCT r1.name AS r1name, l1.gateway AS r1ip, '
            + 'r2.name AS r2name, l2.gateway as r2ip, v.vid AS vid, '
            + 'LENGTH(shortestPath((sn)<-[:ROUTED|ROUTED_BY|ROUTED_STANDBY*0..12]->(r1))) '
            + 'AS distance ORDER BY distance',
            {"net1": net1, "net2": net2, "vrf": popt['VRF']})

        allpaths = dict()
        # Load all paths into tuples with distance value
        for rec in rtrp:
            p = (rec["r1name"], rec["r2name"])
            allpaths[p] = rec["distance"]


        # Find tuple with shortest distance (r1, core1) vs (core1, r1)
        # Save to pathRec for second pass of records to populate tree
        for en in allpaths:
            if allpaths[en] < allpaths[tuple(reversed(en))]:
                (r1, r2) = en
                distance = allpaths[en]
                pathRec.append((r1, r2, distance))

        # Sort path records by distance, src router, dst router
        pathRec = sorted(pathRec, key=lambda tup: (tup[2], tup[0], tup[1]))

        # Build Trees and pathList from pathRecs
        for path in pathRec:
            for rec in rtrp:
                if path[0] == rec['r1name'] and path[1] == rec['r2name']:
                    #print(path[0], rec['r1ip'], '-->', path[1], rec['r2ip'])
                    rtree = nglib.ngtree.get_ngtree("Hop", tree_type="L3-HOP")
                    rtree['From Router'] = rec['r1name']
                    rtree['From IP'] = rec['r1ip']
                    rtree['To Router'] = rec['r2name']
                    rtree['To IP'] = rec['r2ip']
                    rtree['VLAN'] = rec['vid']

                    # Calculate hop distance
                    # Distance of 1 is correct, other distances should be:
                    #   ((dist - 1) / 2) + 1
                    distance = rec['distance']
                    if distance != 1:
                        distance = int((distance - 1) / 2) + 1

                    # Save distance
                    rtree['distance'] = distance

                    # Rename rtree
                    rtree['Name'] = "#{:} {:}({:}) -> {:}({:})".format( \
                    distance, rec['r1name'], rec['r1ip'], rec['r2name'], rec['r2ip'])

                    if 'VLAN' in rtree and rtree['VLAN'] != '0':
                        rtree['Name'] = rtree['Name'] + ' [vid:' + str(rtree['VLAN']) + ']'

                    # Add Switchpath if requested
                    if popt['l2path']:
                        spath = get_switched_path(rec['r1name'], rec['r2name'], popt)
                        if spath:
                            for sp in spath:
                                if '_child' in sp and '_rvlans' in spath[sp]:
                                    vrgx = r'[^0-9]*' + rec['vid'] + '[^0-9]*'
                                    if re.search(vrgx, spath[sp]['_rvlans']):
                                        nglib.ngtree.add_child_ngtree(rtree, spath[sp])
                                    # else:
                                    #     print(spath[sp]['_rvlans'])
                                    # nglib.ngtree.add_child_ngtree(rtree, spath[sp])

                    # Single / Multi-path
                    if not popt['onepath'] or distance not in hopSet:
                        hopSet.add(distance)
                        nglib.ngtree.add_child_ngtree(ngtree, rtree)
                    pathList.append(rtree)

        # Check Results
        if pathList:

            ngtree['Hops'] = len(pathList)
            ngtree['Distance'] = max([s['distance'] for s in pathList])
            ngtree['VRF'] = popt['VRF']

            if popt['onepath']:
                ngtree['Traversal Type'] = 'Single Path'
                ngtree['Traversal Coverage'] = path_coverage(ngtree['Distance'], ngtree['Hops'])
            else:
                ngtree['Traversal Type'] = 'All Paths'

            # CSV Prints locally for now
            if rtype == "CSV":
                nglib.query.print_dict_csv(pathList)

            # Export NG Trees
            else:
                # Export NGTree
                ngtree = nglib.query.exp_ngtree(ngtree, rtype)
                return ngtree
        elif popt['verbose']:
            print("No results found for path between {:} and {:}".format(net1, net2), \
                file=sys.stderr)


def get_switched_path(switch1, switch2, popt, rtype="NGTREE"):
    """
    Find the path between two switches and return all interfaces and
    devices between the two.

    - Uses Neo4j All Shortest Paths on NEI Relationships
    - Returns all distinct links along shortest paths along with distance

    Notes: Query finds all shortest paths between two Switch nodes. Then finds
    all links between individual nodes and gets both switch and port names. Data
    is sorted by distance then switch name.
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:


        if 'onepath' not in popt:
            popt['onepath'] = False
        if 'verbose' not in popt:
            popt['verbose'] = True

        if popt['verbose']:
            logger.info("Query: Finding Switched Paths (%s --> %s) for %s",
                        switch1, switch2, nglib.user)

        pathList = []
        hopSet = set()
        ngtree = nglib.ngtree.get_ngtree("Switched Paths", tree_type="L2-PATH")
        ngtree["Name"] = str(switch1) + " -> " + str(switch2)

        swp = nglib.py2neo_ses.cypher.execute(
            'MATCH (ss:Switch), (ds:Switch), '
            + 'sp = allShortestPaths((ss)-[:NEI|NEI_EQ*0..9]-(ds)) '
            + 'WHERE ss.name =~ {switch1} AND ds.name =~ {switch2}'
            + 'UNWIND nodes(sp) as s1 UNWIND nodes(sp) as s2 '
            + 'MATCH (s1)<-[nei:NEI|NEI_EQ]-(s2), plen = shortestPath((ss)-[:NEI*0..9]-(s1)) '
            + 'RETURN DISTINCT s1.name AS csw, s2.name AS psw, '
            + 'nei.pPort AS pport, nei.cPort as cport, nei.native AS native, '
            + 'nei.cPc as cPc, nei.pPc AS pPc, nei.vlans AS vlans, nei.rvlans as rvlans, '
            + 'nei._rvlans AS p_rvlans, '
            + 'LENGTH(plen) as distance ORDER BY distance, s1.name, s2.name',
            {"switch1": switch1, "switch2": switch2})

        # Process records
        last = 0
        for rec in swp:
            swptree = nglib.ngtree.get_ngtree("Link", tree_type="L2-HOP")

            # Fix distance from directed graph and add From -> To
            if rec.distance == 0:
                swptree['distance'] = rec.distance + 1
                swptree['_reverse'] = 1
                last = 1
            elif last:
                if rec.distance == last:
                    last += 1
                    swptree['distance'] = rec.distance + 1
                    swptree['_reverse'] = 1
                elif rec.distance == (last-1):
                    swptree['distance'] = rec.distance + 1
                    swptree['_reverse'] = 1
                else:
                    swptree['distance'] = rec.distance
                    swptree['_reverse'] = 0
                    last = 0
            else:
                swptree['distance'] = rec.distance
                swptree['_reverse'] = 0

            swptree['Child Switch'] = rec.csw
            swptree['Child Port'] = rec.cport
            swptree['Parent Switch'] = rec.psw
            swptree['Parent Port'] = rec.pport

            if rec.cPc:
                swptree['Child Channel'] = rec.cPc
                swptree['Parent Channel'] = rec.pPc
            if rec.rvlans:
                swptree['Link VLANs'] = rec.vlans
                swptree['Link rVLANs'] = rec.rvlans
                swptree['_rvlans'] = rec.p_rvlans
                swptree['Native VLAN'] = rec.native

            # Add directions to traversal and update name
            if 'Parent Switch' in swptree:
                swptree = spath_direction(swptree)

            # Save data structures
            if not popt['onepath'] or swptree['distance'] not in hopSet:
                hopSet.add(swptree['distance'])
                nglib.ngtree.add_child_ngtree(ngtree, swptree)

            # App Paths go in pathlist
            pathList.append(swptree)

        if pathList:

            ngtree['Links'] = len(pathList)
            ngtree['Distance'] = max([s['distance'] for s in pathList])

            if popt['onepath']:
                ngtree['Traversal Type'] = 'Single Path'
                ngtree['Traversal Coverage'] = path_coverage(ngtree['Distance'], ngtree['Links'])
            else:
                ngtree['Traversal Type'] = 'All Paths'

            # CSV Prints locally for now
            if rtype == "CSV":
                nglib.query.print_dict_csv(pathList)

            # Export NG Trees
            else:
                # Export NGTree
                ngtree = nglib.query.exp_ngtree(ngtree, rtype)
                return ngtree
        elif popt['verbose']:
            print("No results found for path between {:} and {:}".format(switch1, switch2))

    return


def spath_direction(swp):
    """ Adds directionality to spath queries
        All spath queries traverse the directed paths from the core out
        Examine _reverse value for reversal of From -> To
    """

    nswp = dict()
    reverse = swp['_reverse']

    for en in swp:
        if 'Child' in en:
            if reverse:
                nen = en.replace('Child', 'From')
                nswp[nen] = swp[en]
            else:
                nen = en.replace('Child', 'To')
                nswp[nen] = swp[en]
        elif 'Parent' in en:
            if reverse:
                nen = en.replace('Parent', 'To')
                nswp[nen] = swp[en]
            else:
                nen = en.replace('Parent', 'From')
                nswp[nen] = swp[en]
        else:
            nswp[en] = swp[en]

    # Update Name
    nswp['Name'] = '#' + str(swp['distance']) + ' ' + \
    nswp['From Switch'] + '(' + nswp['From Port'] +  ') -> ' \
    + nswp['To Switch'] + '(' + nswp['To Port'] + ')'

    if 'From Channel' in nswp and nswp['From Channel'] != '0':
        nswp['Name'] = nswp['Name'] + ' [pc:' + nswp['From Channel'] \
            + '->' + nswp['To Channel'] + ']'

    return nswp


def path_coverage(inc, total):
    """ Return the path coverage percentage for partial paths"""
    perc = (inc * 100.0) / total
    (percent) = str(perc).split('.')
    return percent[0] + '%'


def get_fw_path(src, dst, popt, rtype="TEXT"):
    """Discover the Firewall Path between two IP addresses"""

    rtypes = ('TEXT', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        if 'onepath' not in popt:
            popt['onepath'] = False
        if 'verbose' not in popt:
            popt['verbose'] = True

        if popt['verbose']:
            logger.info("Query: Security Path %s -> %s for %s", src, dst, nglib.user)

        logcmd = nglib.config['nglib']['logcmd']
        logurl = nglib.config['nglib']['logurl']

        srcnet = nglib.query.net.find_cidr(src)
        dstnet = nglib.query.net.find_cidr(dst)


        if nglib.verbose:
            print("\nFinding security path from {:} -> {:}:\n".format(srcnet, dstnet))

        # Shortest path between VRFs
        path = nglib.py2neo_ses.cypher.execute(
            'MATCH (s:Network { cidr:{src} })-[e1:VRF_IN]->(sv:VRF), '
            + '(d:Network {cidr:{dst}})-[e2:VRF_IN]->(dv:VRF), '
            + 'p = shortestPath((sv)-[:VRF_IN|ROUTED_FW|:SWITCHED_FW*0..20]-(dv)) RETURN s,d,p',
            src=srcnet, dst=dstnet)

        fwsearch = dict()

        ngtree = nglib.ngtree.get_ngtree("Security Path", tree_type="L4-PATH")

        # Go through all nodes in the path
        if len(path) > 0:
            for r in path.records:
                sn = r.s
                snp = nglib.query.nNode.getJSONProperties(sn)
                dn = r.d
                dnp = nglib.query.nNode.getJSONProperties(dn)

                path = ""

                # Path
                nodes = r.p.nodes
                for node in nodes:
                    nProp = nglib.query.nNode.getJSONProperties(node)
                    label = nglib.query.nNode.getLabel(node)
                    tlabel = re.search(r'(\w+)', label)
                    hop = nglib.ngtree.get_ngtree(tlabel.group(1), tree_type="L4-HOP")
                    if re.search('VRF', label):
                        path = path + "VRF:" + nProp['name'] + " -> "
                        hop['_type'] = "L4VRF"

                    if re.search('FW', label):
                        path = path + nProp['name'] + " -> "
                        fwsearch[nProp['name']] = nProp['hostname'] + "," + nProp['logIndex']
                        hop['Name'] = nProp['name']
                        hop['_type'] = "L4FW"

                    # Network Hop
                    elif re.search('Network', label):
                        hop['Name'] = nProp['cidr']
                        hop['_type'] = "L4GW"

                        # Add properties
                        #router = get_router(nProp)
                        if 'vid' and 'vrf' in nProp:
                            hop['Name'] = hop['Name'] + ' [rtr:' + get_router(nProp) \
                                + ' vid:' + nProp['vid'] \
                                + ' vrf:' + nProp['vrf'] + ']'
                            #hop['Name'] = hop['Name'] + ' VRF:' + nProp['vrf']

                    for prop in nProp:
                        hop[prop] = nProp[prop]
                    nglib.ngtree.add_child_ngtree(ngtree, hop)

                # Save the Path
                ngtree['Name'] = re.search(r'(.*)\s->\s$', path).group(1)
                path = snp['cidr'] + " -> " + path + dnp['cidr']

                # Text output for standalone query
                if rtype == "TEXT":
                    print("\nSecurity Path: " + path)

                    for fw in fwsearch.keys():
                        (hostname, logIndex) = fwsearch[fw].split(',')

                        # Splunk Specific Log Search, may need site specific adjustment
                        cmd = "{:} 'index={:} host::{:} {:} {:}'".format(
                            logcmd, logIndex, hostname, src, dst)
                        query = 'index={:} host::{:} {:} {:}'.format(
                            logIndex, hostname, src, dst)

                        query = query.replace(" ", "%20")

                        print("\n{:} (15min): {:}{:}".format(fw, logurl, query))

                        if popt['verbose']:
                            print(cmd)

                        proc = subprocess.Popen(
                            [cmd + " 2> /dev/null"],
                            stdout=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)

                        (out, err) = proc.communicate()

                        if err:
                            print(err)
                        elif out:
                            print(out)

                    # Space out
                    print()

            # Export NGTree
            ngtree = nglib.query.exp_ngtree(ngtree, rtype)
            return ngtree

def get_router(ngtree):
    """ Return router and standby router properties if they exist"""

    router = ""
    if 'Router' in ngtree:
        router = ngtree['Router']
    if 'StandbyRouter' in ngtree:
        router = router + '|' + ngtree['StandbyRouter']
    return router
