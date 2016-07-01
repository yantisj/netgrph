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
NetGrph Device Import Library (Routers and Switches)
Also contains NEI import routines
"""
import csv
import re
import logging
import nglib

logger = logging.getLogger(__name__)

verbose = 0
dist_exclude = "NOEXCLUDEDEFINED"


def import_devicelist(fileName, infoFile):
    """Import Devices from Devices.csv"""

    logger.info("Importing Devices from %s, %s", fileName, infoFile)
    time = nglib.get_time()

    # Get Seed devices for CDP Direction
    seed = dict()
    seeds = nglib.dev_seeds.split(',')

    for s in seeds:
        seed[s] = True

    f = open(fileName)
    devdb = csv.DictReader(f)

    # Import Location Info
    df = open(infoFile)
    infodb = csv.DictReader(df)

    locdb = dict()

    for en in infodb:
        locdb[en['Device']] = en['Location']

    for en in devdb:

        device = en['Device']
        group = en['MgmtGroup']
        if group == "None":
            group = None
        rType = en['Type']

        # Location Data
        location = 'Unknown'
        if device in locdb.keys():
            location = locdb[device]


        if rType == "Primary":
            if verbose > 3:
                print("R: " + device)
            import_router(device, group, time, seed, rType, location)

        elif rType == "Standby":
            if verbose > 3:
                print("Rs: " + device)
            import_router(device, group, time, seed, rType, location)
        else:
            if verbose > 3:
                print("S: " + device)
            import_switch(device, group, time, seed, location)


def import_switch(switch, group, time, seed, location):
    """ Import single switch (ignores switches without MGMT Group)"""

    distance = nglib.max_distance

    # Get Seed Status
    isSeed = 0
    if switch in seed.keys():
        isSeed = 1
        distance = 0

    # Only import switches with MGMT Group (switch,mgmtgroup=GROUP)
    if group:

        result = nglib.py2neo_ses.cypher.execute(
            'MATCH (s:Switch {name:{switch}}) return s',
            switch=switch)

        # New Switch, insert
        if len(result) == 0:
            logger.info("New: Inserting %s INTO switch, s:%s d:%s", switch, isSeed, distance)

            nglib.py2neo_ses.cypher.execute(
                'CREATE (s:Switch {name:{switch}, distance:{distance}, seed:{seed}, '
                + 'mgmt:{group}, loation:{location}, time:{time}}) return s',
                switch=switch, seed=isSeed, distance=distance, group=group,
                location=location, time=time)
        else:
            logger.debug("Switch Exists %s", switch)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (s:Switch {name:{switch}}) SET s += '
                + '{time:{time}, seed:{seed}, mgmt:{group}, location:{location}} RETURN s',
                switch=switch, seed=isSeed, group=group, location=location, time=time)

        # Update Distance on Node from Seed
        update_distance(switch)

    else:
        logger.debug("Skipping: No Management Group for Switch: " + switch)


def import_router(router, group, time, seed, rType, location):
    """ Import routers from devlicelist.csv format"""

    distance = nglib.max_distance

    # Standby Status
    standby = 0
    if rType == "Standby":
        standby = 1

    # Get Seed Status
    isSeed = 0
    if router in seed.keys():
        isSeed = 1
        distance = 0

    # Routers always get imported, but if no MgmtGroup, import as Unknown
    if not group:
        group = "Unknown"

    rtrSearch = 'MATCH(r:Switch {name:{router}}) return r.router AS router'
    result = nglib.py2neo_ses.cypher.execute(rtrSearch, router=router)

    # New Router, insert
    if len(result) == 0:
        logger.info("New: Inserting %s INTO router", router)

        nglib.py2neo_ses.cypher.execute(
            'CREATE (r:Switch:Router {name:{router}, seed:{seed}, distance:{distance}, '
            + 'standby:{standby}, mgmt:{group}, location:{location}, time:{time}})',
            router=router, seed=isSeed, distance=distance, location=location,
            standby=standby, group=group, time=time)

    else:
        logger.debug("Router Exists %s, updating timestamp", router)
        nglib.py2neo_ses.cypher.execute(
            'MATCH (s:Switch:Router {name:{router}}) SET s += '
            + '{time:{time},seed:{seed},standby:{standby}, '
            + 'location:{location}, mgmt:{group}} RETURN s',
            router=router, seed=isSeed, standby=standby, group=group,
            location=location, time=time)

    # Map all routers to default VRF
    link_router_to_vrf(router, "default")

    # Update Distance on Node from Seed
    update_distance(router)


def link_router_to_vrf(router, vrf):
    """Create a link from a router to a VRF (called from net_update now)"""

    time = nglib.get_time()

    result = nglib.py2neo_ses.cypher.execute(
        'MATCH( s:Switch:Router {name:{router}})<-[r:VRF_ON]-'
        + '(v:VRF {name:{vrf}}) RETURN r',
        router=router, vrf=vrf)

    if len(result) == 0:
        logger.info("New: Creating VRF_ON Relationship %s to %s", router, vrf)

        nglib.py2neo_ses.cypher.execute(
            'MATCH (r:Switch:Router {name:{router}}), (v:VRF {name:{vrf}}) '
            + 'CREATE (r)<-[e:VRF_ON {time:{time}}]-(v)',
            router=router, vrf=vrf, time=time)
    else:
        logger.debug("Debug: %s already linked to VRF %s, updating timestamp",
                     router, vrf)

        result = nglib.py2neo_ses.cypher.execute(
            'MATCH( s:Switch:Router {name:{router}})<-[r:VRF_ON]-(v:VRF {name:{vrf}}) ' +
            'SET r += {time:{time}} RETURN r',
            router=router, vrf=vrf, time=time)



def reseed_neighbors():
    """
    Set all Switch nodes back to nglib.max_distance and set seed nodes to 0
    Clear all Neighbor Relationships
    """

    logger.info("Reseeding all Switches and Deleting all Neighbors")

    # Reset all Distance Values to Default
    nglib.py2neo_ses.cypher.execute(
        'MATCH (s:Switch) SET s.distance={max_distance} RETURN s',
        max_distance=nglib.max_distance)

    # Reset Seeds to Distance 0
    nglib.py2neo_ses.cypher.execute(
        'MATCH (s:Switch) WHERE s.seed = 1 SET s.distance=0 RETURN s')

    # Clear all NEI and NEI_EQ Relationships
    nglib.py2neo_ses.cypher.execute(
        'MATCH(s:Switch)-[e:NEI|NEI_EQ]-() DELETE e')



def import_neighbors(fileName):
    """Find if neighbors are adjacent, if so, links them"""

    logger.info("Importing Neighbors from " + fileName)

    f = open(fileName)
    ndb = csv.DictReader(f)
    time = nglib.get_time()

    for en in ndb:

        localName = en['LocalName']
        localPort = en['LocalPort']
        remoteName = en['RemoteName']
        remotePort = en['RemotePort']

        # Exclude Management Ports
        exPorts = '(mgmt|FastEthernet)'
        if re.search(exPorts, localPort) or re.search(exPorts, remotePort):
            logger.debug("Skipping NEI: " + remoteName)
        else:
            if verbose > 2:
                print("Debug importNeighbors", localName, localPort, remoteName,
                      remotePort)

            checkLocal = nglib.py2neo_ses.cypher.execute(
                'MATCH (s:Switch {name:{name}}) RETURN '
                + 's.distance AS distance, s.seed AS seed',
                name=localName)

            checkRemote = nglib.py2neo_ses.cypher.execute(
                'MATCH (s:Switch {name:{name}}) RETURN s.distance AS distance, s.seed AS seed',
                name=remoteName)

            # Found two neighbors, import
            if len(checkLocal) and len(checkRemote):

                # Get Distances
                localD = checkLocal.records[0].distance
                remoteD = checkRemote.records[0].distance

                import_adjacent_neighbors(en, localD, remoteD, time)


def import_adjacent_neighbors(en, localD, remoteD, time):
    """
    Import Neighbors if both are found in DB

    Notes: Only link from parent -> child
           Link Equal Distance Neighbors only once
    """

    localName = en['LocalName']
    localPort = en['LocalPort']
    remoteName = en['RemoteName']
    remotePort = en['RemotePort']

    # Parent Child Neighbor, Never link distance free nodes
    if remoteD > localD and localD < nglib.max_distance:
        logger.debug("Debug: Found Neighbor with Higher Distance %s --> %s",
                     localName, remoteName)

        existingNei = nglib.py2neo_ses.cypher.execute(
            'MATCH (l:Switch {name:{local}})'
            + '-[e:NEI {pPort:{localPort}, cPort:{remotePort}}]'
            + '-(r:Switch {name:{remote}}) RETURN r',
            local=localName, remote=remoteName, localPort=localPort,
            remotePort=remotePort)

        if len(existingNei) > 0:
            logger.debug("Updated NEI %s:%s --> %s:%s",
                         localName, localPort, remoteName, remotePort)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (l:Switch {name:{local}})'
                + '-[e:NEI {pPort:{localPort}, cPort:{remotePort}}]'
                + '->(r:Switch {name:{remote}})'
                + 'SET e += {time:{time}, pSwitch:{local}, cSwitch:{remote}} RETURN e',
                local=localName, time=time, remote=remoteName, localPort=localPort,
                remotePort=remotePort)

        else:
            logger.info("New: Creating NEI Relationship %s --> %s",
                        localName, remoteName)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (r:Switch {name:{local}}), (s:Switch {name:{remote}}) '
                + 'CREATE (r)-[e:NEI {time:{time}, pSwitch:{local}, pPort:{localPort}, '
                + 'cSwitch:{remote}, cPort:{remotePort}}]->(s)',
                local=localName, time=time, remote=remoteName, localPort=localPort,
                remotePort=remotePort)

    # Equal Neighbors
    elif remoteD == localD and localD < nglib.max_distance:
        logger.debug("Debug: Found Neighbor with Equal Distance %s --> %s",
                     localName, remoteName)

        # NEI_EQ can be bidirectional, only allow one
        existingNei1 = nglib.py2neo_ses.cypher.execute(
            'MATCH (l:Switch {name:{local}})'
            + '-[e:NEI_EQ {pPort:{localPort}, cPort:{remotePort}}]'
            + '->(r:Switch {name:{remote}}) RETURN r',
            local=localName, local1=localName, remote=remoteName,
            localPort=localPort, remotePort=remotePort)

        # Bidirectional Check, don't do anything if matches
        existingNei2 = []

        existingNei2 = nglib.py2neo_ses.cypher.execute(
            'MATCH (l:Switch {name:{local}})'
            + '<-[e:NEI_EQ {cPort:{localPort}, pPort:{remotePort}}]'
            + '-(r:Switch {name:{remote}}) RETURN r',
            local=localName, remote=remoteName,
            localPort=localPort, remotePort=remotePort)

        # Only allow a single relationship between equal nodes, don't import bidirectional
        if len(existingNei1) > 0 and len(existingNei2) == 0:
            logger.debug("Updated NEI_EQ %s:%s --> %s:%s",
                         localName, localPort, remoteName, remotePort)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (l:Switch {name:{local}})'
                + '-[e:NEI_EQ {pPort:{localPort}, cPort:{remotePort}}]'
                + '-(r:Switch {name:{remote}})'
                'SET e += {time:{time}, pSwitch:{local}, cSwitch:{remote}} RETURN e',
                local=localName, time=time, remote=remoteName,
                localPort=localPort, remotePort=remotePort)

        # New Bidirectional Relationship
        elif len(existingNei1) == 0 and len(existingNei2) == 0:
            logger.info("New: Creating NEI_EQ Relationship %s --> %s",
                        localName, remoteName)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (s:Switch {name:{local}}), (r:Switch {name:{remote}}) '
                + 'CREATE (s)-[e:NEI_EQ {time:{time}, pSwitch:{local}, pPort:{localPort}, '
                + 'cSwitch:{remote}, cPort:{remotePort}}]->(r)',
                local=localName, time=time, remote=remoteName,
                localPort=localPort, remotePort=remotePort)


def update_distance(switch):
    """ Update the distance Value of a Switch node from seed node"""

    # Exclude these switches in distance calculation
    # From config[topology][dist_exclude]
    exclude = re.search(dist_exclude, switch)

    # Excluded switches stay with default value
    if not exclude:

        # Find Neighbors to this node and get their distance
        nei = nglib.py2neo_ses.cypher.execute(
            'MATCH (l:Switch {name:{switch}})-[e:NEI]-(r:Switch) '
            + 'RETURN l.seed AS seed, l.distance AS ldist, r.distance AS rdist',
            switch=switch)

        # If neighbors exist
        if len(nei) > 0:


            # Start with lowest distance of default
            lowDist = nglib.max_distance

            # Start local distance value equal to current distance
            distance = nei.records[0].ldist

            # Skip calculations on seed devices
            if nei.records[0].seed != 1:

                newdist = distance

                # Look through neighbors for distance values
                for r in nei.records:
                    # Find the lowest distance neighbor
                    if int(r.rdist) < lowDist:
                        lowDist = r.rdist

                # If Local Distance is more than 1 greater than lowest distance,
                # update distance to be rdist+1
                if distance > (lowDist + 1):
                    newdist = lowDist + 1
                # If the local distance is too low, update it
                elif distance <= (lowDist):
                    newdist = lowDist + 1

                #Update the distance to be 1 + lowDist
                if distance != newdist and newdist < nglib.max_distance:
                    logger.info("New: Switch Distance: %s (%s-->%s)",
                                switch, distance, newdist)

                    nglib.py2neo_ses.cypher.execute(
                        'MATCH (s:Switch {name:{switch}}) SET s.distance={newdist} RETURN s',
                        switch=switch, newdist=newdist)


# FIXME (as dictionary)
def import_vrfs(fileName):
    """Import VRFs from CSV"""

    logger.info("Importing VRFs from " + fileName)

    vrfs = open(fileName)

    for line in vrfs:
        line = line.strip()
        en = line.split(',')

        if len(en) > 2:
            vrf = en[0]
            seczone = en[1]
            desc = en[2]
            import_single_vrf(vrf, seczone, desc)


def import_single_vrf(vrf, seczone=0, desc=None):
    """Import a single VRF in to the database"""

    time = nglib.get_time()
    result = nglib.py2neo_ses.cypher.execute(
        'MATCH (v:VRF {name:{vrf}}) RETURN v',
        vrf=vrf)

    # Insert new VRF
    if len(result) == 0:
        logger.info("Creating new VRF: " + vrf)

        nglib.py2neo_ses.cypher.execute(
            'CREATE (v:VRF {name:{vrf}, seczone:{seczone}, time:{time}, desc:{desc}})',
            vrf=vrf, seczone=seczone, time=time, desc=desc)

    else:
        logger.debug("Updating Existing VRF: " + vrf)

        nglib.py2neo_ses.cypher.execute(
            'MATCH (v:VRF {name:{vrf}}) '
            + 'SET v.seczone={seczone}, v.time={time}, v.desc={desc}',
            vrf=vrf, seczone=seczone, time=time, desc=desc)
