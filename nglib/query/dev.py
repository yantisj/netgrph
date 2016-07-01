#!/usr/bin/env python
#
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
Device Query Routines

"""
import logging
import nglib
import nglib.ngtree
import nglib.ngtree.export

logger = logging.getLogger(__name__)

verbose = 0

# FIXME (Break up queries)
def get_device(dev, rtype="TREE", vrange=None):
    """Get Switch perspective (neighbors, vlans, routed networks)"""

    vlow = None
    vhigh = None
    if vrange:
        (vlow, vhigh) = nglib.query.vlan.get_vlan_range(vrange)

    rtypes = ('TREE', 'JSON', 'YAML')

    if rtype not in rtypes:
        raise Exception("Selected RType not allows for this query", rtype)

    ngtree = nglib.ngtree.get_ngtree(dev, tree_type="Device")

    logger.info("Query: Device %s for %s", dev, nglib.user)


    switch = nglib.bolt_ses.run(
        'MATCH (s:Switch {name:{dev}})'
        + 'RETURN s.name as name, s.distance as distance,s.mgmt as mgmt',
        {"dev": dev})

    for sw in switch:

        ngtree['Distance'] = int(sw['distance'])
        ngtree['MGMT Group'] = sw['mgmt']
        if vrange:
            ngtree['VLAN Range'] = vrange

        ## Find VRFs
        vrfs = nglib.bolt_ses.run(
            'MATCH (s:Switch {name:{dev}})<-[:VRF_ON]-(v:VRF) RETURN v.name AS name',
            {"dev": dev})

        vrflist = []
        for vrf in vrfs:
            vrflist.append(vrf['name'])

        if len(vrflist):
            ngtree['VRFs'] = vrflist


        ## Find all neighbors and build tree
        neighbors = nglib.bolt_ses.run(
            'MATCH (s:Switch {name:{dev}})-[e:NEI|:NEI_EQ]-(rs:Switch) '
            + 'RETURN rs.name AS name, rs.distance AS distance, rs.mgmt as mgmt,'
            + 'e.pSwitch AS pSwitch, e.pPort as pPort, e.cSwitch as cSwitch, e.cPort as cPort '
            + 'ORDER BY distance,name',
            {"dev": dev})

        # Nest Parents, Siblings and Children
        #ntree = nglib.ngtree.get_ngtree(sw['name'], tree_type="Neighbors")
        p_nei = nglib.ngtree.get_ngtree(sw['name'], tree_type="NEI Parents")
        e_nei = nglib.ngtree.get_ngtree(sw['name'], tree_type="NEI Equals")
        c_nei = nglib.ngtree.get_ngtree(sw['name'], tree_type="NEI Children")
        (neicount, p_count, e_count, c_count) = (0, 0, 0, 0)

        for nei in neighbors:
            neicount = neicount + 1
            nei_distance = int(nei['distance'])
            cngt = nglib.ngtree.get_ngtree(nei['name'], tree_type="Neighbor")

            # Parent
            if nei_distance < ngtree['Distance']:
                nglib.ngtree.add_child_ngtree(p_nei, cngt)
                p_count = p_count + 1
            elif nei_distance == ngtree['Distance']:
                nglib.ngtree.add_child_ngtree(e_nei, cngt)
                e_count = e_count + 1
            else:
                nglib.ngtree.add_child_ngtree(c_nei, cngt)
                c_count = c_count + 1


            #nglib.ngtree.add_child_ngtree(ntree,cngt)

            cngt['Distance'] = nei['distance']
            cngt['MGMT Group'] = nei['mgmt']
            cngt['parent_switch'] = nei['pSwitch']
            cngt['parent_port'] = nei['pPort']
            cngt['child_switch'] = nei['cSwitch']
            cngt['child_port'] = nei['cPort']

        if neicount:
            ngtree['Total Neighbors'] = neicount
            if c_count:
                ngtree['Child Neighbors'] = c_count


        # Add Parents and Equals, optionally add children at end
        if p_count:
            ngtree['Parent Neighbors'] = p_count
            nglib.ngtree.add_child_ngtree(ngtree, p_nei)
        if e_count:
            ngtree['Equal Neighbors'] = e_count
            nglib.ngtree.add_child_ngtree(ngtree, e_nei)

        if 0 < c_count <= 4:
            nglib.ngtree.add_child_ngtree(ngtree, c_nei)


        ## Find all networks and build tree
        networks = nglib.bolt_ses.run(
            'MATCH (s:Switch {name:{dev}})<-[e:ROUTED_BY|ROUTED_STANDBY]-(n:Network) '
            + 'RETURN n.cidr as cidr, n.vid as vid ORDER BY toInt(vid)',
            {"dev": dev})

        nettree = nglib.ngtree.get_ngtree(sw['name'], tree_type="Networks")
        netcount = 0

        for net in networks:
            if not vrange or vlow <= int(net['vid']) <= vhigh:
                netcount = netcount + 1
                nettree = nglib.query.net.get_net_extended_tree(net['cidr'], ngtree=nettree)

        if netcount:
            ngtree['Network Count'] = netcount
            nglib.ngtree.add_child_ngtree(ngtree, nettree)


        ## Find all VLANs on a Switch
        vlans = nglib.bolt_ses.run(
            'MATCH (s:Switch {name:{dev}})<-[e:Switched]-(v:VLAN) '
            + 'RETURN v.name AS name, e.desc AS desc, v.vid AS vid, '
            + 'e.pcount AS pcount, e.mcount AS mcount ORDER BY toInt(vid)',
            {"dev": dev})

        vtree = nglib.ngtree.get_ngtree(sw['name'], tree_type="VLANs")
        vcount = 0
        # Build VTrees
        for vlan in vlans:
            if not vrange or vlow <= int(vlan['vid']) <= vhigh:
                vcount = vcount+1
                vt = nglib.ngtree.get_ngtree(vlan['name'], tree_type="VLAN")
                nglib.ngtree.add_child_ngtree(vtree, vt)

                vt['Description'] = vlan['desc']
                if vlan['pcount']:
                    vt['Port Count'] = vlan['pcount']
                if vlan['mcount']:
                    vt['MAC Count'] = vlan['mcount']

        if vcount:
            ngtree['VLAN Count'] = vcount
            nglib.ngtree.add_child_ngtree(ngtree, vtree)

        # Add child neighbors late if more than 4
        if neicount > 4:
            nglib.ngtree.add_child_ngtree(ngtree, c_nei)

        # Export Results
        nglib.query.exp_ngtree(ngtree, rtype)
        return ngtree
