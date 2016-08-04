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

"""Process Alerts for different network events"""

import configparser
import smtplib
import logging
from email.mime.text import MIMEText
#from email.mime.multipart import MIMEMultipart
import nglib

verbose = 0
logger = logging.getLogger(__name__)

# Generate Alerts on new networks
def gen_new_network_alerts():
    """Generate New Network Alerts"""

    gAlert = dict()
    newNets = []

    # Find any new networks
    results = nglib.py2neo_ses.cypher.execute(
        'MATCH(n:NewNetwork) return n.vrfcidr AS vrfcidr')

    ncount = len(results)

    if ncount > 0:
        logger.info("Found %s New Networks to Alert On", ncount)

        # Load groups in to dictionary to add list of networks to
        loadGroups(gAlert)

        # Append all networks to a list
        for network in results:
            #print(network.vrfcidr)
            newNets.append(network.vrfcidr)

        # Filter Nets for each group and add to their list to alert
        loadNetAlerts(gAlert, newNets)

        # Send Alerts to each group
        for g in gAlert.keys():
            if verbose > 1:
                print("\n\nALERTS for {0}:\n".format(g))
            acount = len(gAlert[g])
            logger.info("Sending %s New Network Alerts to %s", acount, g)

            if not verbose:
                sendEmailAlert(g, gAlert[g])

    # Deleting NewNetwork Objects
    if not verbose:
        results = nglib.py2neo_ses.cypher.execute(
            'MATCH(n:NewNetwork) delete n')

def gen_new_vlan_alerts():
    """ Send new VLAN Alerts to all groups that receive 'all' alerts """

    newVlans = []
    groups = []

    # Find any new networks
    results = nglib.py2neo_ses.cypher.execute(
        'MATCH(v:NewVLAN) return v.name AS name')

    ncount = len(results)

    if ncount > 0:
        logger.info("Found %s New Vlans to Alert On", ncount)

        #
        for group in nglib.config['NetAlertGroups']:
            if nglib.config['NetAlertFilter'][group] == 'all':
                groups.append(group)

        # Append all vlans to a list
        for vlan in results:
            newVlans.append(vlan.name)

            if nglib.verbose:
                print(groups)
                print(newVlans)

        for group in groups:
            sendEmailAlert(group, newVlans, vlan=True)
        
        # Deleting NewVLAN Objects
        if not verbose:
            results = nglib.py2neo_ses.cypher.execute(
                'MATCH(n:NewVLAN) delete n')

def loadGroups(gAlert):
    """Load all groups from config file into a dictionary of lists"""

    for group in nglib.config['NetAlertGroups']:
        gAlert[group] = []


def loadNetAlerts(gAlert, newNets):
    """Add networks to each group after filtering attributes"""

    for net in newNets:

        netDict = nglib.query.net.get_net_props(net)

        if len(netDict.keys()):
            for group in gAlert.keys():
                if nglib.query.check_net_filter(netDict, group):
                    logger.debug("Adding " + netDict['CIDR'] + " to alerts for " + group)
                    gAlert[group].append(netDict)


def sendEmailAlert(group, nList, vlan=False):
    """Send group Network Alert from matched list"""

    if nglib.verbose:
        print("Emailing {0} New Network List Alert:\n {1}".format(group, str(nList)))

    emailAddress = nglib.config['NetAlertGroups'][group]
    fromAddress = nglib.config['NetAlert']['from']    
    mailServer = nglib.config['NetAlert']['mailServer']
    subject = nglib.config['NetAlert']['subject']

    if vlan:
        subject = nglib.config['NetAlert']['vlansubject']

    nTable = ""

    for n in nList:
        nTable = nTable + "\n" + str(n)

    nTable = "<br />".join(nTable.split("\n"))

    contents = '<font face="Courier New, Courier, monospace">' + nTable + '</font>'

    msg = MIMEText(contents, 'html')
    msg['Subject'] = subject
    msg['From'] = fromAddress
    msg['To'] = emailAddress

    s = smtplib.SMTP(mailServer)
    s.sendmail(fromAddress, [emailAddress], msg.as_string())
    s.quit()

    if nglib.verbose:
        print(emailAddress, fromAddress, subject, contents)

# END
