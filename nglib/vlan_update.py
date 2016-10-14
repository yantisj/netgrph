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
#
#
"""NetGrph VLAN Import and Topology routines"""

import logging
import csv
from collections import defaultdict
import nglib
import nglib.query.dev

logger = logging.getLogger(__name__)


def import_vlans(fileName, ignore_new=False):
    """Import a list of VLANs for every switch"""

    logger.info("Importing List of VLANs from " + fileName)

    vdb = nglib.importCSVasDict(fileName)

    # Import all VLAN nodes and link to MGMT Group
    import_mgmt_vlan(vdb, ignore_new)

    logger.info("Linking VLANs to Switches")

    vdb = nglib.importCSVasDict(fileName)

    # Link VLAN to Switch
    for en in vdb:
        link_vlan_switch(en)


def link_vlan_switch(en):
    """Link a VLAN to a Switch (Bolt Driver)"""

    time = nglib.get_time()

    vname = en['MGMT'] + "-" + en['VID']
    desc = en['VName']
    switch = en['Switch']
    stp = en['STP']

    results = nglib.bolt_ses.run(
        'MATCH (n:VLAN {name:{vname}})-[e:Switched]->(s:Switch {name:{switch}}) '
        + 'RETURN n.name AS name',
        {"vname": vname, "switch": switch})

    # Check for Results FIXME
    try:
        name = next(iter(results))
        logger.debug("Updating: VLAN (%s)-[:Switched]->(%s) Relationship", vname, switch)

    except:
        logger.info("New: VLAN (%s)-[:Switched]->(%s) Relationship", vname, switch)

    nglib.bolt_ses.run(
        'MATCH (v:VLAN {name:{vname}}), (s:Switch {name:{switch}}) ' +
        'MERGE (v)-[e:Switched]->(s) SET e += {desc:{desc}, stp:{stp}, time:{time}} RETURN e',
        {"vname": vname, "switch": switch, "desc": desc, "stp": stp, "time": time})


def import_mgmt_vlan(vdb, ignore_new):
    """Collate all MGMT-VID pairs, insert nodes and link to MgmtGroup"""


    vuniq = dict()

    time = nglib.get_time()

    for en in vdb:
        vname = en['MGMT'] + "-" + en['VID']
        vuniq[vname] = 1

    for en in vuniq.keys():
        vname = en
        (mgmt, vid) = vname.split('-')
        vid = str(vid)

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:VLAN {name:{vname}}) RETURN n',
            vname=vname)

        # Add new VLAN
        if len(results) == 0:
            logger.info("New: Inserting VLAN %s", en)

            results = nglib.py2neo_ses.cypher.execute(
                'CREATE (v:VLAN {name:{vname}, vid:{vid}, mgmt:{mgmt}, time:{time}}) RETURN v',
                vname=vname, vid=vid, mgmt=mgmt, time=time)

            # Record New Network Unless Ignoring initial run
            if not ignore_new:
                # Store a NewVLAN Object for alerting
                nglib.py2neo_ses.cypher.execute(
                    'CREATE (v:NewVLAN {name:{vname}, time:{time}}) RETURN v',
                    vname=vname, time=time)

        # Else update record
        else:
            logger.debug("Updating VLAN %s", vname)
            nglib.py2neo_ses.cypher.execute(
                'MATCH (v:VLAN {name:{vname}}) SET v += '
                + '{vid:{vid}, mgmt:{mgmt}, time:{time}} RETURN v',
                vname=vname, vid=vid, mgmt=mgmt, time=time)


def import_links(fileName):
    """Read in all trunk links from fileName
       Load vlans for all switches into cache
       Find the intersecting vlans between trunk interfaces
       Find the intersecting vlans between switches
       Find the intersection between vlans that can exist on trunk
       Add vlans to interface relationship
    """

    logger.info("Importing Trunk Links from " + fileName)

    f = open(fileName)
    lcsv = csv.DictReader(f)
    ldb = dict()
    vcache = cache_vlans()

    # Load CSV entries into ldb dict
    for en in lcsv:
        ldb[(en['Switch'],en['Port'])] = en

    # Get all links on network
    links = nglib.bolt_ses.run('MATCH(ps)-[e:NEI|NEI_EQ]->(cs) ' +
                               'RETURN ps.name, e.pPort, cs.name, e.cPort')

    for en in links:

        pname = en['ps.name']
        pport = en['e.pPort']
        cname = en['cs.name']
        cport = en['e.cPort']

        # Both sides of the link are in the LDB
        if (pname, pport) in ldb and (cname, cport) in ldb:

            # Set of intersected VLANs between two trunks
            iset = intersect_vlans(ldb[(pname, pport)]['vlans'], \
            ldb[(cname, cport)]['vlans'])

            rset = set()

            # If VLAN exists on both switches and is in trunk, then it traverses link
            for v in iset:
                if int(v) in vcache[pname] and int(v) in vcache[cname]:
                    rset.add(v)

            if nglib.verbose>3:
                print("ps", ldb[(pname, pport)]['vlans'])
                print("cs", ldb[(cname, cport)]['vlans'])
                print("pvc", vcache[pname])
                print("cvc", vcache[cname])
            if nglib.verbose>2:
                print("ON LINK", sorted(rset), "on", pname, pport, cname, cport)

            # Convert set to sorted vstring
            rlist = []
            for en in sorted(rset):
                rlist.append(str(en))
            vstring = ','.join(rlist)

            # No Vlans on trunk
            if not vstring and nglib.verbose>1:
                print("No VLANS", pname, pport, cname, cport)
                print("ps", ldb[(pname, pport)]['vlans'])
                print("cs", ldb[(cname, cport)]['vlans'])
                print("pvc", vcache[pname])
                print("cvc", vcache[cname])

            # Update Link Info
            pldb = ldb[(pname, pport)]
            pldb['_rvlans'] = vstring
            pldb['rvlans'] = compact_vlans(rset)
            pldb['cvlans'] = compact_vlans(iset)
            cldb = ldb[(cname, cport)]
            #print("Update Info", pname, pport, cname, cport, pldb, cldb )
            add_vlans_int(pldb, cldb)

        else:
            if nglib.verbose>1:
                print("Link not found in ldb", (pname, pport), (cname, cport))


def cache_vlans():
    """Build a VLAN Cache from each switch"""

    vcache = defaultdict(set)

    vlans = nglib.bolt_ses.run(
        'MATCH(s:Switch)<-[e:Switched]-(v) ' +
        'RETURN s.name, v.vid')

    for v in vlans:
        vcache[v['s.name']].add(int(v['v.vid']))

    return vcache


def intersect_vlans(set1, set2):
    """Reduce VLANS to common range, returns set"""

    set1 = expand_vlans(set1)
    set2 = expand_vlans(set2)

    iset = set(set1).intersection(set2)
    return iset


def expand_vlans(oset):
    """Expand a VLAN range to a set"""

    lset = oset.split(',')
    nset = set()

    # Process vlan ranges eg. 1,2,3-20,4,5 into set
    for en in lset:
        sset = en.split('-')
        if len(sset) > 1:
            for x in range(int(sset[0]), int(sset[1])+1):
                nset.add(x)
        elif en:
            nset.add(int(en))

    return nset


def compact_vlans(oset):
    """Convert set of vlans to range format"""

    last = 0
    crange = 0
    nset = []

    for en in sorted(oset):
        if last and en == (last+1):
            if not crange:
                crange = last
        elif crange:
            nset.pop()
            nset.append(str(crange) + '-' + str(last))
            crange = 0
            nset.append(str(en))
        else:
            nset.append(str(en))
        last = en

    if crange:
        nset.pop()
        nset.append(str(crange) + '-' + str(last))

    #print("os", sorted(oset), "rs", nset)

    return ",".join(nset)

def add_vlans_int(pldb, cldb):
    """Add VLAN Info to link pldb->cldb"""

    nglib.bolt_ses.run(
        'MATCH (ps:Switch {name:{pname}})-'
        + '[e:NEI|NEI_EQ {pPort:{pPort}, cPort:{cPort}}]->'
        + '(cs:Switch {name:{cname}}) '
        + 'SET e += {desc:{desc}, native:{nv}, pPc:{pPc}, cPc:{cPc}, '
        + 'vlans:{cvlans}, rvlans:{rvlans}, _rvlans:{_rvlans}} RETURN e',
        {"pname": pldb['Switch'], "pPort": pldb['Port'], "cname": cldb['Switch'],
         "cPort": cldb['Port'], "desc": pldb['desc'], "nv": pldb['native'],
         "pPc": pldb['channel'], "cPc": cldb['channel'], "cvlans": pldb['cvlans'],
         "rvlans": pldb['rvlans'], "_rvlans": pldb['_rvlans']})


def update_vlans():
    """Run VLAN update routines"""

    logger.info("Updating VLAN Topology (Descriptions, Bridges, and Roots)")

    # Update descriptions
    if nglib.verbose:
        logger.info("Updating Descriptions")
    update_vlan_desc()

    # Update Bridge Domains
    if nglib.verbose:
        logger.info("Updating Bridge Domains")
    update_bridge_domains()

    # Root election
    root_election()


def root_election():
    """Kick off a root election for VLANs"""

    # Find the local root for each switch domain
    if nglib.verbose:
        logger.info("Local Switch Domain Root Election")
    find_local_root()

    # Search all bridge trees for lowest STP and link the root domain to the root
    if nglib.verbose:
        logger.info("Bridged Switch Domain Root Election")
    find_bridged_root()


def update_vlan_desc():
    """Update VLAN descriptions using election process on each switch in domain"""

    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN) RETURN v.name as vname')

    # Get all VLANs
    if len(results) > 0:
        for v in results:
            vname = v.vname
            descdb = dict()
            topDesc = 'Unknown'

            # Get vlan desc properties for each switch from relationship
            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (v:VLAN {name:{vname}})-[e:Switched]-() RETURN e.desc AS desc',
                vname=vname)

            # Get all descriptions from relationships to switches and count them
            if len(results) > 0:
                for d in results:
                    desc = d.desc
                    if desc != "NONAME":
                        if desc not in descdb.keys():
                            descdb[desc] = 1
                        else:
                            descdb[desc] = descdb[desc] + 1

            # Top Value Found
            if descdb.keys():
                topDesc = max(descdb.keys())

            if nglib.verbose > 2:
                logger.debug("Updating top description for VLAN:%s Desc:%s", vname, topDesc)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (v:VLAN {name:{vname}}) SET v.desc={topDesc} RETURN v',
                vname=vname, topDesc=topDesc)


def update_bridge_domains():
    """Update all vlan bridges between vlan management domains"""

    # Get all Switches and their child neighbors
    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (ps:Switch)-[e:NEI|NEI_EQ]->(cs:Switch) '
        + 'RETURN ps.name as pswitch, ps.mgmt AS pmgmt, cs.name as cswitch, '
        + 'cs.mgmt AS cmgmt, e._rvlans AS rvlans')

    if len(results) > 0:
        for r in results.records:

            # Different MGMT Domain and adjacent, look to bridge VLANs
            if r.pmgmt != r.cmgmt:

                # Get all VIDs for both parent and child switches
                pvlans = nglib.py2neo_ses.cypher.execute(
                    'MATCH (ps:Switch {name:{pswitch}})<-[e:Switched]-(v:VLAN) '
                    + 'RETURN v.vid as vid',
                    pswitch=r.pswitch)
                cvlans = nglib.py2neo_ses.cypher.execute(
                    'MATCH (ps:Switch {name:{cswitch}})<-[e:Switched]-(v:VLAN) '
                    + 'RETURN v.vid as vid',
                    cswitch=r.cswitch)

                # Bridge VLANs across MGMT Domains if they exist on link
                if len(pvlans) > 0 and len(cvlans) > 0:
                    pvdb = dict()
                    cvdb = dict()
                    rvlans = set()
                    if r.rvlans:
                        rvlans = set(r.rvlans.split(','))

                    # Load dicts of vlan IDs both both parent and child
                    for p in pvlans.records:
                        pvdb[p.vid] = 1
                    for c in cvlans.records:
                        cvdb[c.vid] = 1

                    # If VIDs Match between parent and child across mgmt domains,
                    # bridge the two
                    for vlan in pvdb.keys():
                        if vlan in cvdb.keys():
                            if vlan in rvlans:
                                update_bridge(r.pmgmt, r.cmgmt, vlan, r.pswitch, r.cswitch)
                            elif nglib.verbose>1:
                                logger.debug("Switches adjacent, missing rvlans to bridge: " +
                                             "v:%s, ps:%s, cs:%s, rv:%s",
                                             vlan, r.pswitch, r.cswitch, rvlans)


def update_bridge(pmgmt, cmgmt, vlan, pswitch, cswitch):
    """Insert or Update a VLAN BRIDGE"""

    if nglib.verbose > 2:
        print("Bridge: ", pmgmt, cmgmt, vlan, pswitch, cswitch)

    pvlan = pmgmt + "-" + vlan
    cvlan = cmgmt + "-" + vlan
    time = nglib.get_time()

    # See if a Bridge Exists
    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (pv:VLAN {name:{pvlan}})-[e:BRIDGE]-(cv:VLAN {name:{cvlan}}) RETURN e',
        pvlan=pvlan, cvlan=cvlan)

    if len(results) == 0:
        logger.info("New: Bridge (%s)-[:BRIDGE]->(%s) Relationship", pvlan, cvlan)

        nglib.py2neo_ses.cypher.execute(
            'MATCH (pv:VLAN {name:{pvlan}}), (cv:VLAN {name:{cvlan}}) '
            + 'CREATE (pv)-[e:BRIDGE {pswitch:{pswitch}, cswitch:{cswitch}, time:{time}}]'
            + '->(cv) RETURN e',
            pvlan=pvlan, cvlan=cvlan, pswitch=pswitch, cswitch=cswitch, time=time)

    else:
        logger.debug("Updating VLAN %s-[:BRIDGE]-%s Relationship", pvlan, cvlan)

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (pv:VLAN {name:{pvlan}})-[e:BRIDGE]-(cv:VLAN {name:{cvlan}}) '
            + 'SET e += {time:{time}} RETURN e',
            pvlan=pvlan, cvlan=cvlan, pswitch=pswitch, cswitch=cswitch, time=time)


def find_local_root():
    """
    Go through every Switch in a management domain
    Find the lowest STP value and assume root within domain
    """

    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN)-[:Switched]->() RETURN DISTINCT(v.name) AS name, v.vid AS vid')

    # Find the local root for vid on each switch
    if len(results) > 0:
        for v in results.records:
            vname = v.name
            stpmin = 32768
            switch = None

            # Get STP values from all Switched Relationships
            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (v:VLAN {name:{vname}})-[e:Switched]->(s) '
                + 'RETURN e.stp AS stp, s.name AS switch ORDER BY switch',
                vname=vname)

            # Find the lowest value
            for s in results.records:
                stp = int(s.stp)
                if stp < stpmin and stp != 0:
                    stpmin = stp
                    switch = s.switch
                    if nglib.verbose > 3:
                        print("Local Root: ", vname, stp, switch)

            # Update VLAN with lowest value
            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (v:VLAN {name:{vname}}) SET v += {lroot:{switch}, lstp:{stp}}',
                vname=vname, switch=switch, stp=stpmin)


def find_bridged_root():
    """Go through each VLAN, search all BRIDGED nodes for lowest STP value"""

    # Get all VLANs
    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN) RETURN v.name AS name')

    if len(results) > 0:
        for r in results.records:
            vname = r.name
            stp = 32768
            rootSwitch = None

            # Find Bridged VLANs first
            bridged = nglib.py2neo_ses.cypher.execute(
                'MATCH (v:VLAN {name:{vname}})-[e:BRIDGE*]-(b:VLAN) '
                + 'RETURN b.name AS name, b.lstp AS lstp, b.lroot AS lroot',
                vname=vname)

            # Local Values
            local = nglib.py2neo_ses.cypher.execute(
                'MATCH (v:VLAN {name:{vname}}) '
                + 'RETURN v.name AS name, v.lstp AS lstp, v.lroot AS lroot, v.vid as vid',
                vname=vname)

            dup = 32768
            if len(bridged) > 0:
                for b in bridged:

                    # New Lowest STP Domain
                    if int(b.lstp) < stp:
                        #print("Low STP: ",vname,b.name,b.lstp,b.lroot)
                        stp = int(b.lstp)
                        dup = stp
                    elif int(b.lstp) == stp:
                        dup = stp

            # Check local stp values
            if len(local) > 0:
                v = local.records[0]

                # If local root is the root for the BRIDGE domain, create root relationship
                if int(v.lstp) <= stp:
                    stp = int(v.lstp)
                    rootSwitch = v.lroot
                    vid = v.vid

                    # Link Bridge domain to root
                    if stp < 32768:
                        if nglib.verbose > 3:
                            print("Low STP: ", vname, stp, rootSwitch)
                        link_vlan_to_root(vname, stp, rootSwitch)
                        if stp != dup:
                            update_bridge_direction(vname, vid, rootSwitch)
                        elif nglib.verbose:
                            logger.info("Duplicate Root Found across another domain:"
                                        + " %s rs:%s", vname, rootSwitch)


def link_vlan_to_root(vname, stp, rootSwitch):
    """Create a VLAN -[ROOT]-> Switch Relationship"""

    root = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VLAN {name:{vname}})-[e:ROOT]-(s:Switch {name:{rootSwitch}}) RETURN e',
        vname=vname, rootSwitch=rootSwitch)

    time = nglib.get_time()

    # Create New Root Relationship
    if len(root) == 0:
        logger.info("New: Root for VLAN (%s)-[:ROOT]->(%s)", vname, rootSwitch)

        nglib.py2neo_ses.cypher.execute(
            'MATCH (v:VLAN {name:{vname}}),(s:Switch {name:{rootSwitch}}) '
            + 'CREATE (v)-[e:ROOT {stp:{stp}, time:{time}}]->(s) RETURN e',
            vname=vname, rootSwitch=rootSwitch, stp=stp, time=time)

    # Update existing
    else:
        logger.debug("Updating Root for VLAN (%s)-[:ROOT]->(%s)", vname, rootSwitch)

        nglib.py2neo_ses.cypher.execute(
            'MATCH (v:VLAN {name:{vname}})-[e:ROOT]->(s:Switch {name:{rootSwitch}}) '
            + 'SET e += {stp:{stp}, time:{time}} RETURN e',
            vname=vname, rootSwitch=rootSwitch, stp=stp, time=time)


def update_bridge_direction(vname, vid, rootSwitch):
    """Find all directionless bridges and fix directions towards root
       Keeps a cache of reversed directions
    """

    rmgmt = nglib.query.dev.get_mgmt_domain(rootSwitch)
    revcache = dict()

    # All directionless bridges
    bridges = nglib.bolt_ses.run(
        'MATCH(v:VLAN {name:{vname}})-[e:BRIDGE*]-(rv) RETURN rv.name as name',
        {"vname": vname})

    for en in bridges:

        # Remote VLAN name
        rv = en['name']

        # Path from remote vlan to root switch
        rpath = nglib.bolt_ses.run(
            'MATCH(v:VLAN {name:{vname}}), (s:Switch {name:{rswitch}}), '
            + 'p = shortestPath((s)-[e:BRIDGE|ROOT*0..20]-(v)) '
            + 'RETURN e, LENGTH(p) as dist',
            {"vname": rv, "rswitch": rootSwitch})

        # Compares direction of path to root, reverses wrong directions
        for rec in rpath:
            lastm = rmgmt
            for b in rec['e']:
                props = b.properties
                if 'pswitch' in props:
                    cmgmt = nglib.query.dev.get_mgmt_domain(props['pswitch'])
                    if vname not in revcache \
                        and lastm != cmgmt:
                        reverse_bridge(vid, props['pswitch'], props['cswitch'])
                        revcache[vname] = 1
                    lastm = nglib.query.dev.get_mgmt_domain(props['cswitch'])


def reverse_bridge(vid, pswitch, cswitch):
    """Reverse Direction of BRIDGE links towards root"""

    logger.info("Update: Reversing Bridge Direction: %s %s %s", vid, pswitch, cswitch)

    current = nglib.bolt_ses.run(
        'MATCH(pv:VLAN {vid:{vid}})-'
        + '[e:BRIDGE {pswitch:{pswitch}, cswitch:{cswitch}}]'
        + '->(cv {vid:{vid}}) RETURN pv.name as pvname, cv.name as cvname, e.time as time',
        {"vid":vid, "pswitch":pswitch, "cswitch":cswitch})

    for rec in current:
        nglib.bolt_ses.run(
            'MATCH(pv:VLAN {vid:{vid}})-'
            + '[e:BRIDGE {pswitch:{pswitch}, cswitch:{cswitch}}]'
            + '->(cv {vid:{vid}}) DELETE e',
            {"vid":vid, "pswitch":pswitch, "cswitch":cswitch})

        nglib.bolt_ses.run(
            'MATCH(pv:VLAN {name:{pvname}}), (cv {name:{cvname}}) '
            + 'CREATE (cv)-[e:BRIDGE '
            + '{pswitch:{cswitch}, cswitch:{pswitch}, time:{time}, test:{pswitch}}]->(pv)',
            {"pvname":rec['pvname'], "cvname":rec['cvname'], "pswitch":pswitch, "cswitch":cswitch, "time":rec['time']})


def netdb_vlan_import():
    """For all (switch, vlan) entries, get mac and port counts"""

    logger.info("Update: Importing MAC and Ports Counts on VLANs from NetDB")

    switchvlans = nglib.bolt_ses.run(
        'MATCH (v:VLAN)-[e:Switched]->(s:Switch) '
        + 'RETURN s.name AS switch, v.vid AS vid, v.name AS vname')

    for en in switchvlans:

        (pcount, mcount) = nglib.netdb.get_mac_and_port_counts(en['switch'], en['vid'])

        nglib.bolt_ses.run(
            'MATCH (v:VLAN {name:{vname}})-[e:Switched]->(s:Switch {name:{switch}}) '
            + 'SET e += {pcount:{pcount}, mcount:{mcount}} RETURN e',
            {"vname": en['vname'], "switch": en['switch'], "pcount": pcount, "mcount": mcount})

# END
