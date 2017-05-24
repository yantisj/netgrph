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
#
#
""" NetGrph Network Import Routines """

import ipaddress
import logging
import nglib

logger = logging.getLogger(__name__)

# Keep a global vrf cache for performance when matching routers to VRFs
vrf_cache = dict()

def import_networks(fileName, ignore_new=False):
    """
    Import CSV File of networks

    Format: Subnet,VLAN,VRF,Router,MGMT Group,Description,Location
    """

    logger.info("Importing List of Networks from " + fileName)

    # Remap default VRFs for devices in config
    vrfmap = dict()
    try:
        for key in nglib.config['default_vrf']:
            #print(key, config['default_vrf'][key])
            vrfmap[key] = nglib.config['default_vrf'][key]
    except KeyError:
        pass

    ndb = nglib.importCSVasDict(fileName)

    for en in ndb:
        import_single_net(en, ignore_new, vrfmap)


def import_single_net(net, ignore_new, vrfmap):
    """Import a CIDR Entry in to NetGrph"""

    time = nglib.get_time()

    router = net['Router']
    gateway = net['Gateway']
    cidr = net['Subnet']
    desc = net['Description']
    vrf = net['VRF']
    vlan = net['VLAN']
    p2p = net['P2P']
    standby = net['Standby']

    # Check VRF Mapping to remap defaults
    if vrf == 'default' and router in vrfmap:
        vrf = vrfmap[router]
        #print("VRF", vrf)

    # Process P2P and Standby Router bools
    if p2p == "True":
        p2p = True
    else:
        p2p = False

    if standby == "True":
        standby = True
    else:
        standby = False

    vrfcidr = '{0}-{1}'.format(vrf, cidr) #unique key

    # Check the Router VRF Cache only once to add new relationship to routers
    check_vrf_cache(router, vrf)

    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (n:Network {vrfcidr:{vrfcidr}}) RETURN n',
        vrfcidr=vrfcidr)

    # Add new network
    if len(results) == 0:
        logger.info("New: Inserting CIDR %s", vrfcidr)

        results = nglib.py2neo_ses.cypher.execute(
            'CREATE (n:Network {cidr:{cidr}, vrfcidr:{vrfcidr}, name:{vrfcidr}, '
            + 'vrf:{vrf}, desc:{desc}, vid:{vlan}, '
            + 'gateway:{gateway}, time:{time}}) RETURN n',
            cidr=cidr, vrfcidr=vrfcidr, vrf=vrf, vlan=vlan, desc=desc, gateway=gateway,
            time=time)

        # Record New Network Unless Ignoring initial run
        if not ignore_new:
            # Store a NewNetwork Object for alerting
            results = nglib.py2neo_ses.cypher.execute(
                'CREATE (n:NewNetwork {cidr:{cidr}, vrfcidr:{vrfcidr}, name:{vrfcidr}, '
                + 'vrf:{vrf}, desc:{desc}, vid:{vlan}, gateway:{gateway}, time:{time}}) RETURN n',
                cidr=cidr, vrfcidr=vrfcidr, vrf=vrf, vlan=vlan, desc=desc,
                gateway=gateway, time=time)

    # Else update record
    else:
        logger.debug("Updating CIDR in Network %s", vrfcidr)
        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {vrfcidr:{vrfcidr}}) SET n += {desc:{desc}, vid:{vlan}, '
            + 'gateway:{gateway}, time:{time}} RETURN n',
            vrfcidr=vrfcidr, desc=desc, vlan=vlan, gateway=gateway, time=time)



    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:VRF_IN]->() RETURN e',
        vrfcidr=vrfcidr)

    # Member of VRF Edge
    if len(results) == 0:
        logger.info("New: Creating VRF Relationship %s -> %s ", net['Subnet'], net['VRF'])

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {vrfcidr:{vrfcidr}}), (v:VRF {name:{vrf}}) '
            + 'CREATE (n)-[e:VRF_IN]->(v) RETURN e',
            vrfcidr=vrfcidr, vrf=vrf)

    else:
        logger.debug("Found existing VRF Relationship %s -> %s ", net['Subnet'], net['VRF'])

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:VRF_IN]->(v:VRF {name:{vrf}}) '
            + 'SET e.time={time} RETURN e',
            vrfcidr=vrfcidr, vrf=vrf, time=time)

    # Make sure Routed By Primary and not p2p link
    if not standby and not p2p:

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:ROUTED_BY]->'
            + '(r:Switch:Router {name:{router}}) RETURN e',
            vrfcidr=vrfcidr, router=router)

        # New router for network
        if len(results) == 0:
            logger.info("New: Creating Router Relationship "
                        + "{0} -> {1} ".format(net['Subnet'], net['Router']))

            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vrfcidr:{vrfcidr}}), (r:Switch:Router {name:{router}}) '
                + 'CREATE (n)-[e:ROUTED_BY {vrf:{vrf}, time:{time}}]->(r) RETURN e',
                vrfcidr=vrfcidr, vrf=vrf, time=time, router=router)

            if len(results) == 0:
                logger.warning("Failed to Create Router Relationship "
                               + "{0} -> {1} ".format(net['Subnet'], net['Router']))

        # Update relationship timestamp
        else:
            logger.debug("Updating Existing Router Relationship: "
                         + "{0} -> {1}".format(net['Subnet'], net['Router']))

            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:ROUTED_BY]->'
                + '(r:Switch:Router {name:{router}}) '
                + 'SET e += {vrf:{vrf}, time:{time}} RETURN n',
                vrfcidr=vrfcidr, vrf=vrf, router=router, time=time)

    # Standby Router for Network
    elif standby and not p2p:
        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:ROUTED_STANDBY]->'
            + '(r:Switch:Router {name:{router}}) RETURN e',
            vrfcidr=vrfcidr, router=router)

        # New router for network
        if len(results) == 0:
            logger.info("New: Creating Standby Router Relationship "
                        + "{0} -> {1} ".format(net['Subnet'], net['Router']))

            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vrfcidr:{vrfcidr}}), (r:Switch:Router {name:{router}}) '
                + 'CREATE (n)-[e:ROUTED_STANDBY {vrf:{vrf}, time:{time}}]->(r) RETURN e',
                vrfcidr=vrfcidr, vrf=vrf, time=time, router=router)

            if len(results) == 0:
                logger.warning("Failed to Create Router Relationship "
                               + "{0} -> {1} ".format(net['Subnet'], net['Router']))

        # Update relationship timestamp
        else:
            logger.debug("Updating Existing Standby Router Relationship: "
                         + "{0} -> {1}".format(net['Subnet'], net['Router']))

            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:ROUTED_STANDBY]->'
                + '(r:Switch:Router {name:{router}}) SET e += {vrf:{vrf}, time:{time}} RETURN n',
                vrfcidr=vrfcidr, vrf=vrf, router=router, time=time)

    # P2P Routed Network. Use Special ROUTED Label for each VRF
    elif p2p:

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:ROUTED {vrf:{vrf}}]->'
            + '(r:Switch:Router {name:{router}}) RETURN e',
            vrfcidr=vrfcidr, vrf=vrf, router=router)

        # New P2P Relationship for network
        if len(results) == 0:
            logger.info("New: Creating P2P Router Relationship "
                        + "{0} -> {1} ({2})".format(net['Subnet'], net['Router'], vrf))


            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vrfcidr:{vrfcidr}}), (r:Switch:Router {name:{router}}) '
                + 'CREATE (n)-[e:ROUTED {vrf:{vrf}, gateway:{gateway}, time:{time}}]->(r) RETURN e',
                vrfcidr=vrfcidr, vrf=vrf, time=time, gateway=gateway, router=router)

            if len(results) == 0:
                logger.warning("Failed to Create Router Relationship "
                               + "{0} -> {1} ".format(net['Subnet'], net['Router']))

        # Update relationship timestamp
        else:
            logger.debug("Updating Existing P2P Router Relationship: "
                         + "{0} -> {1} ({2})".format(net['Subnet'], net['Router'], vrf))

            results = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {vrfcidr:{vrfcidr}})-[e:ROUTED]->'
                + '(r:Switch:Router {name:{router}}) '
                + 'SET e += {vrf:{vrf}, gateway:{gateway}, time:{time}} RETURN n',
                vrfcidr=vrfcidr, vrf=vrf, router=router, gateway=gateway, time=time)

    # Link up L2 to L3 info
    link_l3_to_l2(vrfcidr, vlan, router, time)

def link_l3_to_l2(vrfcidr, vlan, router, time):
    """Create relationship on from L3 Vlan to L2 Vlan based on router"""
    group = None

    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (n:Network {name:{name}})-[e:L3toL2]->(v:VLAN {vid:{vlan}}) RETURN e',
        name=vrfcidr, vlan=vlan)

    mgmt = nglib.py2neo_ses.cypher.execute(
        'MATCH (s:Switch {name:{router}}) RETURN s.mgmt as mgmt',
        router=router)

    if len(mgmt) > 0:
        group = mgmt.records[0].mgmt

    if len(results) == 0 and group:
        l2vlan = nglib.py2neo_ses.cypher.execute(
            'MATCH (r:Router {name:{name}})<-[e:Switched]-'
            + '(v:VLAN {vid:{vlan}}) RETURN v.name as name',
            name=router, vlan=vlan)

        if len(l2vlan) > 0:

            vname = l2vlan.records[0].name
            #print(vname,vrfcidr,router,vlan)

            logger.info("New: Creating L3toL2 Relationship "
                        + "{0} vid:{1} -> {2} through {3}".format(vrfcidr, vlan, vname, router))

            l2vlan = nglib.py2neo_ses.cypher.execute(
                'MATCH (n:Network {name:{name}}), (v:VLAN {name:{vname}}) '
                + 'CREATE (n)-[e:L3toL2 {time:{time}}]->(v) RETURN e',
                name=vrfcidr, vname=vname, time=time)

    elif len(results) > 0:
        logger.debug("Updating L3toL2 Relationship "
                     + "{0} vid:{1} -> {1} through {2}".format(vrfcidr, vlan, router))

        nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Network {name:{name}})-[e:L3toL2]->(v:VLAN {vid:{vlan}}) '
            + 'SET e += {time:{time}} RETURN e',
            name=vrfcidr, vlan=vlan, time=time)


def check_vrf_cache(router, vrf):
    """Only update VRFs on routers on first hit"""

    global vrf_cache
    rtov = router + "__" + vrf
    if rtov not in vrf_cache:
        vrf_cache[rtov] = 1
        if nglib.verbose > 2:
            print("Added Router to VRF Cache", rtov)
        nglib.dev_update.link_router_to_vrf(router, vrf)


def import_supernets(fileName):
    """
    Import Supernets

    Format: cidr,role,description,secure
    """

    logger.info("Importing Supernets from " + fileName)

    sndb = nglib.importCSVasDict(fileName)

    for en in sndb:
        import_supernet(en)

    # Update Supernet Links
    update_supernet_links()

def import_supernet(snet):
    """Import a Supernet Entry"""

    time = nglib.get_time()

    cidr = snet['cidr']
    desc = snet['description']
    role = snet['role']
    secure = snet['secure']


    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (n:Supernet {cidr:{cidr}}) RETURN n', cidr=cidr)

    # Insert new supernet
    if len(results) == 0:
        logger.info("New: Inserting Supernet: " + cidr)

        results = nglib.py2neo_ses.cypher.execute(
            'CREATE (n:Supernet {cidr:{cidr}, name:{cidr}, desc:{desc}, role:{role}, '
            + 'secure:{secure}, time:{time}}) RETURN n',
            cidr=cidr, role=role, desc=desc, secure=secure, time=time)
    # Update existing Supernet
    else:
        logger.debug("Supernet Exists, updating: " + cidr)
        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (n:Supernet {cidr:{cidr}}) '
            + 'SET n += {desc:{desc}, role:{role}, secure:{secure}, time:{time}} RETURN n',
            cidr=cidr, role=role, desc=desc, secure=secure, time=time)


def update_supernet_links():
    """
    Analyze all networks and create supernet links where CIDR is in
    supernet CIDR
    """

    snet = dict()

    # Load Supernets as dictionary
    results = nglib.py2neo_ses.cypher.execute('MATCH (n:Supernet) RETURN n.cidr as cidr')
    for record in results:
        snet[record.cidr] = 1


    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (n:Network) RETURN n.cidr as cidr, n.vrfcidr as vrfcidr')

    # Scan all networks and try to link to supernet
    for record in results:
        cidr = record.cidr
        if cidr:
            ip = nglib.getEntry(cidr.rsplit('/'))

            # Search through Supernets for cidr match
            for key in snet.keys():

                if ipaddress.ip_address(ip) in ipaddress.ip_network(key):
                    logger.debug(cidr + " in Supernet " + key)

                    # Create or update supernet link
                    superLink(record.vrfcidr, key)


def superLink(vrfcidr, supercidr):
    """Link a vrfcidr to a Supernet"""

    time = nglib.get_time()

    results = nglib.py2neo_ses.cypher.execute(
        'MATCH (sn:Supernet {cidr:{supercidr}})'
        + '<-[e:SUPER]-(n:Network {vrfcidr:{vrfcidr}}) RETURN e',
        vrfcidr=vrfcidr, supercidr=supercidr)

    # Make a new Supernet Link
    if len(results) == 0:
        logger.info("New: Creating %s -[SUPER]-> %s Link", vrfcidr, supercidr)

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (sn:Supernet {cidr:{supercidr}}), (n:Network {vrfcidr:{vrfcidr}}) '
            + 'CREATE (sn)<-[e:SUPER {time:{time}}]-(n) RETURN e',
            vrfcidr=vrfcidr, supercidr=supercidr, time=time)
    else:
        logger.debug("Super Exists: %s -[SUPER]-> %s Link", vrfcidr, supercidr)

        results = nglib.py2neo_ses.cypher.execute(
            'MATCH (sn:Supernet {cidr:{supercidr}})<-[e:SUPER]-'
            + '(n:Network {vrfcidr:{vrfcidr}}) SET e.time={time} RETURN e',
            vrfcidr=vrfcidr, supercidr=supercidr, time=time)
