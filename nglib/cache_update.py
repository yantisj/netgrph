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

"""NetGrph Cache Management"""

import logging
from nglib.query.nNode import getRelationship, getLabel, getJSONProperties
import nglib

logger = logging.getLogger(__name__)


def clear_edges(hours):
    """
    Clear Expired Edges

    Notes: nglib.verbose returns edges to delete but does not delete
    """

    logger.info("Clearing Edges older than " + str(hours) + " hours")

    # Time shifted datetime
    age = nglib.get_time(hours=hours)

    edges = nglib.py2neo_ses.cypher.execute(
        'MATCH ()-[e]->() WHERE e.time < {age} RETURN e',
        age=age)

    if len(edges) > 0:
        for e in edges:
            try:
                neighbors = getRelationship(e.e)
                logger.info("Expired Edge: " + neighbors)
            except ValueError:
                logger.warning('Decoding error on edge clear')

        count = nglib.py2neo_ses.cypher.execute(
            'MATCH ()-[e]->() WHERE e.time < {age} RETURN count(e) as count',
            age=age)

        if nglib.verbose:
            logger.info("Expired Edges: " + str(count[0].count))
        else:
            logger.info("Deleting Edges: " + str(count[0].count))
            nglib.py2neo_ses.cypher.execute(
                'MATCH ()-[e]->() WHERE e.time < {age} DELETE e',
                age=age)


def clear_nodes(hours):
    """
    Clear Expired Nodes

    Notes: verbose returns nodes to delete but does not delete
    """

    logger.info("Finding Nodes to Clear older than " + str(hours) + " hours")

    # Time shifted datetime
    age = nglib.get_time(hours=hours)

    nodes = nglib.py2neo_ses.cypher.execute(
        'MATCH (n) WHERE n.time < {age} RETURN n',
        age=age)

    if len(nodes) > 0:

        for r in nodes:
            label = getLabel(r.n)
            try:
                pj = getJSONProperties(r.n)
                logger.info("Expired Node: " + label + pj['name'])
            except ValueError:
                logger.warning('Decoding error on node clear')

        count = nglib.py2neo_ses.cypher.execute(
            'MATCH (n) WHERE n.time < {age} RETURN count(n) as count',
            age=age)

        logger.info("Expired Nodes: " + str(count[0].count))

        if not nglib.verbose:
            logger.info("Deleting Nodes: " + str(count[0].count))

            nglib.py2neo_ses.cypher.execute(
                'MATCH (n)-[e]-() WHERE n.time < {age} DELETE e',
                age=age)

            nglib.py2neo_ses.cypher.execute(
                'MATCH (n) WHERE n.time < {age} DELETE n',
                age=age)


def swap_quotes(myString):
    """Swap Quote Types for JSON from Neo4j"""
    myString = myString.replace("'", '"')
    return myString
