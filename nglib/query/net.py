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

import ipaddress
import logging
import nglib
import nglib.query
import nglib.netdb.ip

from nglib.query.nNode import getJSONProperties


verbose = 0
logger = logging.getLogger(__name__)


def get_net(ip, rtype="TREE", days=7):
    """Find a network and return text output"""

    rtypes = ('TREE', 'JSON', 'YAML', 'NGTREE')

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
        ngtree = nglib.query.exp_ngtree(ngtree, rtype)
        return ngtree

    else:
        print("Unsupport RType, try", str(rtypes))


def get_net_extended_tree(net, ip=None, ngtree=None, ngname="Networks"):
    """Built a Network ngtree with extended subnet attributes"""

    network = nglib.py2neo_ses.cypher.execute(
        'MATCH (n:Network { cidr:{net} })-[e:ROUTED_BY]->(r) '
        + 'OPTIONAL MATCH (n)-[:ROUTED_STANDBY]->(sr) RETURN n,r,sr',
        net=net)

    subnet = nglib.query.net.get_ipv4net(net)
    if not ngtree:
        ngtree = nglib.ngtree.get_ngtree(ngname, tree_type="Parent")

    matches = dict()

    if len(network) > 0:
        for n in network.records:

            # Get node properties
            nProp = getJSONProperties(n.n)
            rProp = getJSONProperties(n.r)

            standby = None
            if n.sr:
                standby = getJSONProperties(n.sr)['name']

            # Not already found
            if nProp['vrfcidr'] not in matches.keys():
                matches[nProp['vrfcidr']] = 1
                cngt = nglib.ngtree.get_ngtree(nProp['cidr'], tree_type="CIDR")
                nglib.ngtree.add_child_ngtree(ngtree, cngt)
                cngt['vrfcidr'] = nProp['vrfcidr']

                # Get extended results
                pNode = get_net_props(nProp['vrfcidr'])

                subsize = subnet.num_addresses
                subsize = subsize - 2

                if ip:
                    cngt['IP'] = ip
                cngt['Netmask'] = str(subnet.netmask)
                cngt['VRF'] = nProp['vrf']
                cngt['Description'] = nProp['desc']
                cngt['Gateway'] = nProp['gateway']
                cngt['Broadcast'] = str(subnet.broadcast_address)
                cngt['Size'] = str(subsize) + " nodes"
                cngt['Role'] = pNode['NetRole']
                cngt['Security Level'] = pNode['SecurityLevel']
                cngt['Router'] = rProp['name']
                cngt['Location'] = rProp['location']
                if standby:
                    cngt['StandbyRouter'] = standby
                if nProp['vid']:
                    cngt['VLAN'] = nProp['vid']

            elif verbose > 3:
                print("Existing Matches", nProp['vrfcidr'])

    return ngtree


def get_networks_on_group(group, rtype="CSV"):
    """
    Get list of networks as CSV for a group in netgraph.ini
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML')

    if rtype in rtypes:

        logger.info("Query: Network List %s for %s", group, nglib.user)

        netList = []
        ngtree = nglib.ngtree.get_ngtree("Networks", tree_type="NET")
        ngtree['Group'] = group

        try:
            ngtree['Filter'] = nglib.query.get_net_filter(group)
        except KeyError:
            print("Error: No Group Found in Config", group)
            return
        except:
            raise

        # Get all networks
        #networks = nglib.bolt_ses.run('MATCH (n:Network) RETURN n.vrfcidr as vrfcidr')

        networks = nglib.bolt_ses.run(
            'MATCH(n:Network), (n)--(v:VRF), (n)-[:ROUTED_BY]->(r:Switch:Router) '
            + 'OPTIONAL MATCH (n)--(s:Supernet) OPTIONAL MATCH (n)-[:ROUTED_STANDBY]->(rs:Switch:Router) '
            + 'RETURN n.cidr AS CIDR, n.vid AS VLAN, '
            + 'n.gateway as Gateway, n.location as Location, n.desc AS Description, '
            + 'r.name AS Router, rs.name AS StandbyRouter, s.role AS NetRole, v.name as VRF, n.vrfcidr AS vrfcidr, '
            + 'v.seczone AS SecurityLevel ORDER BY CIDR')

        # Check to see if networks match group
        for net in networks:

            # Build a proper dict
            netDict = dict()
            for key in net:
                netDict[key] = net[key]

            # Matches Filter
            if len(netDict) and nglib.query.check_net_filter(netDict, group):

                netList.append(netDict)
                netDict['_type'] = "CIDR"
                netDict['Name'] = netDict['CIDR']

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
            print("No results found for filter:", ngtree['Filter'])

    else:
        raise Exception("RType Not Allowed, try: ", str(rtypes))


def get_networks_on_cidr(cidr, rtype="CSV"):
    """
    Pass in CIDR, get results as a network list
    Refactoring with Bolt Driver (hybrid)
    Notes: Need to convert to get_net_extended_tree but ran in to bugs
    """

    rtypes = ('CSV', 'TREE', 'JSON', 'YAML')

    if rtype in rtypes:

        logger.info("Query: Network CIDRs in %s for %s", cidr, nglib.user)

        netList = []
        ngtree = nglib.ngtree.get_ngtree("IN CIDR", tree_type="NET")
        ngtree['CIDR'] = cidr

        networks = nglib.bolt_ses.run(
            'MATCH (n:Network) RETURN n.gateway AS gateway, n.name AS vrfcidr')

        for net in networks:

            # Check to see if gateway IP within CIDR (subnet boundary won't match)
            if net['gateway']:
                if ipaddress.ip_address(net['gateway']) in ipaddress.ip_network(cidr):

                    netDict = get_net_props(net['vrfcidr'])

                    # # Get extended net tree for subnet and pull out child element
                    # netDict = get_net_extended_tree(net['cidr'])
                    # netDict = netDict['_child001']

                    logging.debug(netDict['CIDR'] + " in Supernet " + cidr)
                    netList.append(netDict)

                    # NGTree
                    netDict['_type'] = "CIDR"
                    netDict['Name'] = netDict['CIDR']

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
        raise Exception("RType Not Allowed, try: ", str(rtypes))



def find_cidr(ip):
    """Finds most specific CIDR in Networks"""

    # Always start with default route
    mostSpecific = "0.0.0.0/0"

    # All networks
    networks = nglib.py2neo_ses.cypher.execute('MATCH (n:Network) RETURN n.cidr as cidr')

    if len(networks) > 1:
        for r in networks.records:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(r.cidr):
                if verbose:
                    print(ip + " in " + r.cidr)
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
        'MATCH(n:Network {vrfcidr:{vrfcidr}}), (n)--(v:VRF), (n)--(r:Switch:Router)'
        + ' OPTIONAL MATCH (n)--(s:Supernet) RETURN n.cidr AS CIDR, n.vid AS VLAN,'
        + ' n.gateway as Gateway, n.location as Location, n.desc AS Description, '
        + 'r.name AS Router, s.role AS NetRole, v.name as VRF, v.seczone AS SecurityLevel',
        {"vrfcidr": vrfcidr})

    for r in result:
        for key in r:
            resultDict[key] = r[key]

    return resultDict
