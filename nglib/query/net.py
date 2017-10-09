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
 NetGrph Query Network data
"""
import sys
import re
import socket
from operator import itemgetter, attrgetter
import ipaddress
import logging
import nglib
import nglib.netdb.ip
from nglib.exceptions import OutputError, ResultError

from nglib.query.nNode import getJSONProperties

logger = logging.getLogger(__name__)


def get_net(ip, rtype="TREE", days=7, verbose=True):
    """Find a network for ip and return text output"""

    rtypes = ('TREE', 'JSON', 'YAML', 'NGTREE')

    if verbose:
        logger.info("Query: Looking up %s for %s", ip, nglib.user)

    if rtype in rtypes:

        net = nglib.query.net.find_cidr(ip)
        ngtree = get_net_extended_tree(net, ip=ip, ngname="IP Object")

        if nglib.use_netdb:
            hours = days * 24
            netdbtree = nglib.netdb.ip.get_netdb_ip(ip, hours=hours)
            if netdbtree:
                nglib.ngtree.add_child_ngtree(ngtree, netdbtree)

        # Export NGTree
        if ngtree:
            ngtree = nglib.query.exp_ngtree(ngtree, rtype)
            return ngtree
        else:
            raise ResultError("No CIDR Results", "IP search failed on %s" % (ip))
    else:
        raise OutputError("RType Not Supported", str(rtypes))


def get_net_extended_tree(net, ip=None, router=None, ngtree=None, ngname="Networks"):
    """Built a Network ngtree with extended subnet attributes

        Accepts cidrs and vrfcidrs (vrf-1.1.1.0/24)
    """

    network = None

    # Specific VRF Query (also matches routed p2p links)
    if re.search(r'^\w+\-\d+', net):

        network = nglib.bolt_ses.run(
            'MATCH (n:Network {vrfcidr:{vrfcidr} })-[er:ROUTED_BY|ROUTED]->(r) '
            + 'OPTIONAL MATCH (n)-[esr:ROUTED_STANDBY]->(sr) RETURN n,r,sr,er,esr',
            {'vrfcidr': net}
        )

        net = net.split('-')[1]
    else:

        network = nglib.bolt_ses.run(
            'MATCH (n:Network {cidr:{cidr} })-[er:ROUTED_BY|ROUTED]->(r) '
            + 'OPTIONAL MATCH (n)-[esr:ROUTED_STANDBY]->(sr) RETURN n,r,sr,er,esr',
            {'cidr': net}
        )

    subnet = nglib.query.net.get_ipv4net(net)
    if not ngtree:
        ngtree = nglib.ngtree.get_ngtree(ngname, tree_type="Parent")

    matches = dict()

    for nn in network:
        n = nn['n']
        r = nn['r']
        sr = nn['sr']
        er = nn['er']
        esr = nn['esr']

        standby = None
        if sr:
            standby = sr['name']

        # Cache: Not already found
        if n['vrfcidr'] not in matches.keys():
            matches[n['vrfcidr']] = 1
            cngt = nglib.ngtree.get_ngtree(n['cidr'], tree_type="CIDR")
            nglib.ngtree.add_child_ngtree(ngtree, cngt)
            cngt['vrfcidr'] = n['vrfcidr']

            subsize = subnet.num_addresses
            subsize = subsize - 2

            # Get extended results
            pNode = get_net_props(n['vrfcidr'])

            if ip:
                cngt['IP'] = ip
            cngt['Netmask'] = str(subnet.netmask)
            cngt['VRF'] = n['vrf']
            cngt['Description'] = n['desc']
            cngt['Gateway'] = n['gateway']
            cngt['Broadcast'] = str(subnet.broadcast_address)
            cngt['Size'] = str(subsize) + " nodes"
            if 'NetRole' in pNode:
                cngt['Role'] = pNode['NetRole']
                cngt['Security Level'] = pNode['SecurityLevel']
            cngt['Router'] = r['name']
            if 'location' in r:
                cngt['Location'] = r['location']
            if standby:
                cngt['StandbyRouter'] = standby
            if n['vid']:
                cngt['VLAN'] = n['vid']
            if n['virtual_proto']:
                cngt['virtual_protocol'] = n['virtual_proto']
                cngt['virtual_version'] = n['virtual_version']
                cngt['virtual_group'] = n['virtual_group']

            if router:
                if router == r['name']:
                    cngt['virtual_priority'] = er['v_prio']
                    cngt['Gateway Physical'] = er['ipv4']
                elif sr and router == sr['name']:
                    cngt['virtual_priority'] = esr['v_prio']
                    cngt['Gateway Physical'] = esr['ipv4']

            cngt['secondary'] = False
            if 'secondary' in n and n['secondary']:
                cngt['secondary'] = True

            if 'virtual_priority' in cngt and not cngt['virtual_priority']:
                cngt.pop('virtual_priority')

        elif nglib.verbose > 3:
            print("Existing Matches", n['vrfcidr'])

    return ngtree


def get_networks_on_filter(group=None, nFilter=None, rtype="NGTREE"):
    """
    Get list of networks as CSV for a group in netgraph.ini
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', 'NGTREE')

    if rtype in rtypes:

        if rtype != "NGTREE":
            logger.info("Query: Network List %s for %s", group, nglib.user)

        netList = []
        ngtree = nglib.ngtree.get_ngtree("Networks", tree_type="NET")

        if group:
            ngtree['Group'] = group

            try:
                ngtree['Filter'] = nglib.query.get_net_filter(group)
            except KeyError:
                print("Error: No Group Found in Config", group)
                return
            except:
                raise

        # Custom Filter
        elif nFilter:
            ngtree['Filter'] = nFilter
        else:
            raise Exception("Must pass in group or nFilter")


        # Get all networks
        networks = nglib.bolt_ses.run(
            'MATCH(n:Network), (n)--(v:VRF), (n)-[er:ROUTED_BY]->(r:Switch:Router) '
            + 'OPTIONAL MATCH (n)--(s:Supernet) OPTIONAL MATCH '
            + '(n)-[esr:ROUTED_STANDBY]->(rs:Switch:Router) '
            + 'RETURN n.cidr AS CIDR, n.vid AS VLAN, '
            + 'n.gateway as Gateway, n.location as Location, n.desc AS Description, '
            + 'r.name AS Router, rs.name AS StandbyRouter, s.role AS NetRole, '
            + 'r.mgmt AS Mgmt, v.name as VRF, n.vrfcidr AS vrfcidr, n.secondary AS secondary, '
            + 'v.seczone AS SecurityLevel, n.virtual_proto AS virtual_protocol, '
            + 'n.virtual_version AS virtual_version, n.virtual_group AS virtual_group ORDER BY CIDR')


        # Sort results by gateway IP
        sort_nets = {}
        for n in networks:
            sort_nets[ipaddress.IPv4Address(n['Gateway'])] = n
        for net in sorted(sort_nets.keys(), key=ipaddress.get_mixed_type_key):
            net = sort_nets[net]

            # Build a proper dict
            netDict = dict()
            for key in net:
                netDict[key] = net[key]

            # Matches Filter
            if len(netDict) and nglib.query.check_net_filter(netDict, group=group, nFilter=nFilter):

                netList.append(netDict)
                netDict['_type'] = "CIDR"
                netDict['Name'] = netDict['CIDR']
                netDict['data'] = []

                # Cleanup Results
                netDict.pop('__values__', None)
                netDict.pop('_ccount', None)
                nglib.ngtree.add_child_ngtree(ngtree, netDict)

        # Check for results
        if '_ccount' in ngtree:
            ngtree['Count'] = ngtree['_ccount']

            # CSV Prints locally for now
            if rtype == "CSV":
                nglib.query.print_dict_csv(netList)

            # Export NG Trees
            else:
                # Export NGTree
                ngtree = nglib.query.exp_ngtree(ngtree, rtype)
                return ngtree
        else:
            print("No results found for filter:", ngtree['Filter'], file=sys.stderr)

    else:
        raise OutputError("RType Not Supported", str(rtypes))


def get_networks_on_cidr(cidr, rtype="CSV"):
    """
    Pass in CIDR, get results as a network list
    Refactoring with Bolt Driver (hybrid)
    Notes: Need to convert to get_net_extended_tree but ran in to bugs
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML', "NGTREE")

    if rtype in rtypes:

        logger.info("Query: Network CIDRs in %s for %s", cidr, nglib.user)

        netList = []
        ngtree = nglib.ngtree.get_ngtree("IN CIDR", tree_type="NET")
        ngtree['CIDR'] = cidr

        networks = nglib.bolt_ses.run(
            'MATCH (n:Network) RETURN n.gateway AS gateway, n.name AS vrfcidr ORDER BY gateway')

        # Sort results by gateway IP
        sort_nets = {}
        for n in networks:
            sort_nets[ipaddress.IPv4Address(n['gateway'])] = n
        for net in sorted(sort_nets.keys(), key=ipaddress.get_mixed_type_key):
            net = sort_nets[net]

            # Check to see if gateway IP within CIDR (subnet boundary won't match)
            if net['gateway']:
                if ipaddress.ip_address(net['gateway']) in ipaddress.ip_network(cidr):

                    netDict = get_net_props(net['vrfcidr'])

                    # # Get extended net tree for subnet and pull out child element
                    if nglib.verbose > 2:
                        logging.debug(netDict['CIDR'] + " in Supernet " + cidr)
                    netList.append(netDict)

                    # NGTree
                    netDict['_type'] = "CIDR"
                    netDict['Name'] = netDict['CIDR']
                    netDict['data'] = []
                    netDict['_ccount'] = 0

                    cleanND = netDict.copy()
                    cleanND.pop('__values__', None)
                    cleanND.pop('_ccount', None)
                    nglib.ngtree.add_child_ngtree(ngtree, cleanND)

        # Results
        if len(netList) > 0:
            ngtree['Count'] = ngtree['_ccount']

            # CSV Handled locally for now
            if rtype == "CSV":
                nglib.query.print_dict_csv(netList)
            # Export NG Trees
            else:
                # Export NGTree
                ngtree = nglib.query.exp_ngtree(ngtree, rtype)
                return ngtree
        else:
            print("No Results for", cidr)

    else:
        raise OutputError("RType Not Supported", str(rtypes))



def find_cidr(ip):
    """Finds most specific CIDR in Networks"""

    # Check for non-ip, try DNS
    if not re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        try:
            ip = socket.gethostbyname(ip)
        except socket.gaierror:
            raise Exception("Hostname Lookup Failure on: " + ip)

    # Always start with default route
    mostSpecific = "0.0.0.0/0"

    # All networks
    networks = nglib.py2neo_ses.cypher.execute('MATCH (n:Network) RETURN n.cidr as cidr')

    if len(networks) > 1:
        for r in networks.records:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(r.cidr):
                if nglib.verbose > 1:
                    print("find_cidr", ip + " in " + r.cidr)
                mostSpecific = compare_cidr(mostSpecific, r.cidr)

    return mostSpecific


def get_ipv4net(cidr):
    """Returns an IPv4Network Object"""

    n = ipaddress.IPv4Network(cidr, strict=True)
    return n


def compare_cidr(first, second):
    """Returns CIDR with the most specific mask"""

    mask1 = first.split('/')
    mask2 = second.split('/')

    if mask1[1] > mask2[1]:
        return first
    else:
        return second


def get_net_props(vrfcidr):
    """Use bolt to get a network returned as a true dict()"""

    resultDict = dict()

    result = nglib.bolt_ses.run(
        'MATCH(n:Network {vrfcidr:{vrfcidr}}), (n)--(v:VRF), (n)--(r:Switch:Router) '
        + 'OPTIONAL MATCH (n)--(s:Supernet) '
        + 'OPTIONAL MATCH (n)-[:ROUTED_BY]->(rb:Switch:Router) '
        + 'OPTIONAL MATCH (n)-[:ROUTED_STANDBY]->(rs:Switch:Router) '
        + 'OPTIONAL MATCH (n)-[:ROUTED]->(rt) '
        + 'RETURN n.cidr AS CIDR, n.vid AS VLAN,'
        + ' n.gateway as Gateway, n.location as Location, n.desc AS Description, '
        + 'r.name AS Router, s.role AS NetRole, v.name as VRF, v.seczone AS SecurityLevel, '
        + 'n.virtual_proto AS virtual_protocol, n.virtual_version AS virtual_version, '
        + 'n.virtual_group AS virtual_group, n.secondary AS secondary, '
        + 'r.mgmt AS Mgmt, rs.name AS StandbyRouter, n.name AS vrfcidr, '
        + 'COLLECT(rt.name) AS routers, rb.name AS routed_by',
        {"vrfcidr": vrfcidr})

    for r in result:
        router = ''
        if r['routed_by']:
            router = r['routed_by']
        else:
            router = r['Router']
        resultDict['Router'] = router
        for key in r:
            if key == 'routers':
                if r['routers']:
                    resultDict[key] = r[key]
            elif key != 'routed_by' and key != 'Router':
                resultDict[key] = r[key]

    return resultDict
