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

verbose = 0


def get_full_path(net1, net2, rtype="NGTREE"):
    """ Gets the full path (switch->rt->VRF->rt->switch)

        Required NetDB for switchpath
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        logger.info("Query: Finding Full Path (%s --> %s) for %s",
                    net1, net2, nglib.user)

        src, dst = net1, net2
        n1tree, n2tree = None, None

        # Translate IPs to CIDRs
        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net1):
            n1tree = nglib.query.net.get_net(net1, rtype="NGTREE")
            if n1tree:
                net1 = n1tree['_child001']['Name']

        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net2):
            n2tree = nglib.query.net.get_net(net2, rtype="NGTREE")
            if n2tree:
                net2 = n2tree['_child001']['Name']

        srctree, dsttree, srcswp, dstswp = None, None, None, None

        if nglib.use_netdb:
            srctree = nglib.netdb.ip.get_netdb_ip(src)
            dsttree = nglib.netdb.ip.get_netdb_ip(dst)
        
        # Find Switched Path from Source to Router
        if srctree:
            router = n1tree['_child001']['Router']
            if 'StandbyRouter' in n1tree['_child001']:
                router = router + '|' + n1tree['_child001']['StandbyRouter']
            srcswp = get_switch_path(srctree['Switch'], router)
        
        # Find Switched Path from Router to Destination
        if dsttree:
            router = n2tree['_child001']['Router']
            if 'StandbyRouter' in n2tree['_child001']:
                router = router + '|' + n2tree['_child001']['StandbyRouter']
            dstswp = get_switch_path(router, dsttree['Switch'])

        switching = True
        # Same switch/vlan check
        if srctree and dsttree:
            if srctree['Switch'] == dsttree['Switch'] and \
                srctree['VLAN'] ==dsttree['VLAN']:
                switching = False

        # Parent Data Structure
        ngtree = nglib.ngtree.get_ngtree("Complete", tree_type="PATHs")
        ngtree["Path"] = src + " -> " + dst

        # Add the SRC Data
        n1tree['_type'] = "SRC"
        n1tree['Name'] = src
        nglib.ngtree.add_child_ngtree(ngtree, n1tree)

        # If there's src switch data
        if srctree and switching:
            if srcswp:
                srcswp['Name'] = "SRC Switched Path"
                nglib.ngtree.add_child_ngtree(ngtree, srcswp)

        # Add the routed path if exists
        rtree = get_routed_path(net1, net2)
        if rtree and switching:
            nglib.ngtree.add_child_ngtree(ngtree, rtree)

        # Destination Switch Data
        if dsttree and switching:
            if dstswp:
                dstswp['Name'] = "DST Switched Path"
                nglib.ngtree.add_child_ngtree(ngtree, dstswp)

        # Add the DST Data
        n2tree['_type'] = "DST"
        n2tree['Name'] = dst
        nglib.ngtree.add_child_ngtree(ngtree, n2tree)

        # Export NGTree
        ngtree = nglib.query.exp_ngtree(ngtree, rtype)
        return ngtree

def get_switch_path(switch1, switch2, rtype="NGTREE"):
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

        logger.info("Query: Finding Switched Paths (%s --> %s) for %s",
                    switch1, switch2, nglib.user)

        pathList = []
        ngtree = nglib.ngtree.get_ngtree("Switched Paths", tree_type="SPATHs")
        ngtree["Path"] = switch1 + " -> " + switch2

        dist = dict()

        swp = nglib.py2neo_ses.cypher.execute(
            'MATCH (ss:Switch), (ds:Switch), '
            + 'sp = allShortestPaths((ss)-[:NEI*0..9]-(ds)) '
            + 'WHERE ss.name =~ {switch1} AND ds.name =~ {switch2}'
            + 'UNWIND nodes(sp) as s1 UNWIND nodes(sp) as s2 '
            + 'MATCH (s1)<-[nei:NEI]-(s2), plen = shortestPath((ss)-[:NEI*0..9]-(s1)) '
            + 'RETURN DISTINCT s1.name AS csw, s2.name AS psw, '
            + 'nei.pPort AS pport, nei.cPort as cport, nei.native AS native, '
            + 'nei.cPc as cPc, nei.pPc AS pPc, nei.vlans AS vlans, nei.rvlans as rvlans, '
            + 'nei._rvlans AS p_rvlans, '
            + 'LENGTH(plen) as distance ORDER BY distance, s1.name, s2.name',
            {"switch1": switch1, "switch2": switch2})


        for rec in swp:
            dist[rec.distance] = 1

        for rec in swp:
            swptree = nglib.ngtree.get_ngtree("Link", tree_type="SPATH")
            nglib.ngtree.add_child_ngtree(ngtree, swptree)

            swptree['Child Switch'] = rec.csw
            swptree['Child Port'] = rec.cport
            swptree['Parent Switch'] = rec.psw
            swptree['Parent Port'] = rec.pport
            swptree['distance'] = rec.distance

            if rec.cPc:
                swptree['Child Channel'] = rec.cPc
                swptree['Parent Channel'] = rec.pPc
            if rec.rvlans:
                swptree['Link VLANs'] = rec.vlans
                swptree['Link rVLANs'] = rec.rvlans
                swptree['_rvlans'] = rec.p_rvlans
                swptree['Native VLAN'] = rec.native


            pathList.append(swptree)

        if pathList:

            ngtree['Links'] = len(pathList)
            ngtree['Distance'] = max([s['distance'] for s in pathList])

            # CSV Prints locally for now
            if rtype == "CSV":
                nglib.query.print_dict_csv(pathList)

            # Export NG Trees
            else:
                # Export NGTree
                ngtree = nglib.query.exp_ngtree(ngtree, rtype)
                return ngtree
        else:
            print("No results found for path between {:} and {:}".format(switch1, switch2))

    return


def get_routed_path(net1, net2, rtype="NGTREE"):
    """
    Find the routed path between two CIDRs and return all interfaces and
    devices between the two. This query need optimization.

    - net1 and net2 can be IPs, and it will find the CIDR
    - Uses Neo4j All Shortest Paths on ROUTED Relationships
    - Returns all distinct links along shortest paths along with distance

    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        logger.info("Query: Finding Routed Paths (%s --> %s) for %s",
                    net1, net2, nglib.user)


        # Translate IPs to CIDRs
        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net1):
            n1tree = nglib.query.net.get_net(net1, rtype="NGTREE")
            net1 = n1tree['_child001']['Name']

        if re.search(r'^\d+\.\d+\.\d+\.\d+$', net2):
            n2tree = nglib.query.net.get_net(net2, rtype="NGTREE")
            if n2tree:
                net2 = n2tree['_child001']['Name']


        ngtree = nglib.ngtree.get_ngtree("Routed Paths", tree_type="RPATHs")
        ngtree["Path"] = net1 + " -> " + net2


        pathList = []
        pathRec = []

        # Finds all paths, then finds the relationships
        rtrp = nglib.py2neo_ses.cypher.execute(
            'MATCH (sn:Network), (dn:Network), rp = allShortestPaths '
            + '((sn)-[:ROUTED|ROUTED_BY|ROUTED_STANDBY*0..12]-(dn)) '
            + 'WHERE ALL(v IN rels(rp) WHERE v.vrf = "default") '
            + 'AND sn.cidr =~ {net1} AND dn.cidr =~ {net2}'
            + 'UNWIND nodes(rp) as r1 UNWIND nodes(rp) as r2 '
            + 'MATCH (r1)<-[l1:ROUTED]-(:Network)-[l2:ROUTED]->(r2) '
            + 'RETURN DISTINCT r1.name AS r1name, l1.gateway AS r1ip, '
            + 'r2.name AS r2name, l2.gateway as r2ip, '
            + 'LENGTH(shortestPath((sn)<-[:ROUTED|ROUTED_BY|ROUTED_STANDBY*0..12]->(r1))) '
            + 'AS distance ORDER BY distance',
            {"net1": net1, "net2": net2})


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
                    rtree = nglib.ngtree.get_ngtree("Hop", tree_type="RPATH")
                    rtree['From Router'] = rec['r1name']
                    rtree['From IP'] = rec['r1ip']
                    rtree['To Router'] = rec['r2name']
                    rtree['To IP'] = rec['r2ip']

                    # Calculate hop distance
                    # Distance of 1 is correct, other distances should be:
                    #   ((dist - 1) / 2) + 1
                    distance = rec['distance']
                    if distance != 1:
                        distance = int((distance - 1) / 2) + 1

                    # Save distance
                    rtree['distance'] = distance

                    nglib.ngtree.add_child_ngtree(ngtree, rtree)
                    pathList.append(rtree)

        # Check Results
        if pathList:

            ngtree['Hops'] = len(pathList)
            ngtree['Max Hops'] = max([s['distance'] for s in pathList])


            # CSV Prints locally for now
            if rtype == "CSV":
                nglib.query.print_dict_csv(pathList)

            # Export NG Trees
            else:
                # Export NGTree
                ngtree = nglib.query.exp_ngtree(ngtree, rtype)
                return ngtree
        else:
            print("No results found for path between {:} and {:}".format(net1, net2), file=sys.stderr)

    return

def get_fw_path(src, dst, rtype="TEXT"):
    """Discover the Firewall Path between two IP addresses"""

    rtypes = ('TEXT', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        logcmd = nglib.config['nglib']['logcmd']
        logurl = nglib.config['nglib']['logurl']

        srcnet = nglib.query.net.find_cidr(src)
        dstnet = nglib.query.net.find_cidr(dst)

        logger.info("Query: Security Tracing %s -> %s for %s", src, dst, nglib.user)

        if verbose:
            print("\nFinding security path from {:} -> {:}:\n".format(srcnet, dstnet))

        # Shortest path between VRFs
        path = nglib.py2neo_ses.cypher.execute(
            'MATCH (s:Network { cidr:{src} })-[e1:VRF_IN]->(sv:VRF), '
            + '(d:Network {cidr:{dst}})-[e2:VRF_IN]->(dv:VRF), '
            + 'p = shortestPath((sv)-[:VRF_IN|ROUTED_FW|:SWITCHED_FW*0..20]-(dv)) RETURN s,d,p',
            src=srcnet, dst=dstnet)

        fwsearch = dict()

        # Go through all nodes in the path
        if len(path) > 0:
            for r in path.records:
                sn = r.s
                snp = nglib.query.nNode.getJSONProperties(sn)
                dn = r.d
                dnp = nglib.query.nNode.getJSONProperties(dn)

                path = snp['cidr'] + " -> "

                # Path
                nodes = r.p.nodes
                for node in nodes:
                    nProp = nglib.query.nNode.getJSONProperties(node)
                    label = nglib.query.nNode.getLabel(node)
                    if re.search('VRF', label):
                        path = path + "VRF:" + nProp['name'] + " -> "

                    if re.search('FW', label):
                        path = path + nProp['name'] + " -> "
                        fwsearch[nProp['name']] = nProp['hostname'] + "," + nProp['logIndex']

                path = path + dnp['cidr']
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

                    if verbose:
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
