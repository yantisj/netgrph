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
"""
NetGrph NetDB Switch Interface
"""
import re
import socket
import logging
import pymysql
import nglib.netdb
import nglib.ngtree

logger = logging.getLogger(__name__)


def get_switch(switch, port='%', hours=720, trunc=True):
    """Get All Interface Details for Switch"""

    # Truncated Values to retrieve
    tr = ['switch', 'port', 'status', 'description', 'vlan', 'speed', 'duplex']

    netdb_ses = nglib.netdb.connect_netdb()
    lastseen = nglib.netdb.get_lastseen(hours)

    cursor = netdb_ses.cursor(pymysql.cursors.DictCursor)

    # cursor.execute("SELECT * FROM superswitch "
    #                + "WHERE ip = '{}' AND lastseen > '{}'".format(switch, lastseen))

    cursor.execute(
        "SELECT switchstatus.switch,switchstatus.port,switchstatus.vlan,switchstatus.status,"
        + "switchstatus.speed,switchstatus.duplex,switchstatus.description,"
        + "switchstatus.p_uptime,switchstatus.p_minutes,switchstatus.lastup,"
        + "superswitch.mac,superswitch.ip,superswitch.s_ip,superswitch.s_name,"
        + "superswitch.name,superswitch.static,superswitch.mac_nd,"
        + "superswitch.vendor,superswitch.vrf,superswitch.router,"
        + "superswitch.uptime,superswitch.minutes,superswitch.firstseen,"
        + "superswitch.lastseen,nacreg.userID,nacreg.firstName,nacreg.lastName,"
        + "nacreg.role,nd.n_host,nd.n_ip,nd.n_desc,nd.n_model,nd.n_port,"
        + "nd.n_protocol,nd.n_lastseen,superswitch.s_speed,superswitch.s_ip,"
        + "superswitch.s_vlan "
        + "FROM switchstatus LEFT OUTER JOIN superswitch "
        + "ON switchstatus.switch = superswitch.switch "
        + "AND switchstatus.port = superswitch.port "
        + "AND superswitch.lastseen > '{}' ".format(lastseen)
        + "LEFT OUTER JOIN neighbor as nd "
        + "ON ( switchstatus.switch = nd.switch AND switchstatus.port = nd.port ) "
        + "LEFT OUTER JOIN nacreg ON nacreg.mac = superswitch.mac "
        + "WHERE (switchstatus.switch like '{}' AND switchstatus.port like '{}') ".format(switch, port)
        + "ORDER BY switchstatus.port"
    )

    pc = cursor.fetchall()

    pngtree = nglib.ngtree.get_ngtree(switch, tree_type="INTs")

    print(dir(pc))

    pseen = dict()

    # Gather details from DB in ngtree structure
    for en in pc:
        ngtree = nglib.ngtree.get_ngtree("INT", tree_type="INT")

        for e in en:
            if e in tr and en['port'] not in pseen:
                ngtree[e] = en[e]

        if en['port'] not in pseen:
            pseen[en['port']] = True
            ngtree['Name'] = ngtree['port']
            nglib.ngtree.add_child_ngtree(pngtree, ngtree)

    return pngtree

def mac(switch, port='%', hours=1):
    """Pull the MAC Table on a switch from NetDB, use switch='%' for everything"""

    netdb_ses = nglib.netdb.connect_netdb()

    lastseen = nglib.netdb.get_lastseen(hours)

    cursor = netdb_ses.cursor(pymysql.cursors.DictCursor)
    # cursor = netdb_ses.cursor(dictionary=True)

    cursor.execute("SELECT * FROM superswitch "
                   + "WHERE switch LIKE '{}' AND port LIKE '{}' ".format(switch, port)
                   + "AND lastseen > '{}'".format(lastseen))

    pc = cursor.fetchall()

    pngtree = nglib.ngtree.get_ngtree("MAC-Table", tree_type="NetDB")

    for en in pc:
        ngtree = nglib.ngtree.get_ngtree("MAC", tree_type="NetDB")

        for f in en:
            ngtree[f] = str(en[f])

        nglib.ngtree.add_child_ngtree(pngtree, ngtree)

    return pngtree

def count(switch, hours=1):
    """ Get the mac address count from a switch """

    netdb_ses = nglib.netdb.connect_netdb()

    lastseen = nglib.netdb.get_lastseen(hours)

    cursor = netdb_ses.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT count(mac) FROM superswitch "
                   + "WHERE switch LIKE '{}' ".format(switch)
                   + "AND lastseen > '{}'".format(lastseen))

    pc = cursor.fetchall()

    pngtree = nglib.ngtree.get_ngtree("MAC-Count", tree_type="NetDB")
    pngtree['switch'] = switch

    for en in pc:
        print(en)
        pngtree['mac_count'] = en['count(mac)']

    return pngtree
