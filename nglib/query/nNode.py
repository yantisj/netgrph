#!/usr/bin/env python
#
# Neo4j py2neo Node and Edge Methods
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
Py2Neo Node Properties (Deprecated)

"""
import logging
import json
import nglib

logger = logging.getLogger(__name__)


def getJSONProperties(node):
    """Returns Properties for a node from JSON as a nested dictionary"""

    json_string = swapQuotes(str(node.properties))
    if nglib.verbose > 1:
        print("JSON:", json_string)
    parsed_json = json.loads(json_string)
    return parsed_json


def getLabel(node):
    """Returns the label in plaintext for a node"""

    label = node.labels.copy()
    label = label.__str__()
    label = label.replace('{', '(')
    label = label.replace('}', ')')

    return label

def getEdge(edge):
    """Return Edge Type"""
    return str(edge.type)

def getRelationship(edge):
    """Get Relationship on edge for printing"""

    snode = edge.start_node
    snodeProp = getJSONProperties(snode)
    enode = edge.end_node
    enodeProp = getJSONProperties(enode)
    relation = getLabel(snode) + "{name:" + snodeProp['name'] + "}-[" + getEdge(edge)
    relation += "]->"  + getLabel(enode) + "{name:" + enodeProp['name'] + "}"

    return relation


def swapQuotes(myString):
    """Swaps single quote with double quotes"""

    myString = myString.replace("'", '"')
    return myString
