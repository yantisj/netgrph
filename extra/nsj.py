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
Netmiko based Sendjob Script
   - Uses NetGrph API for Inventory
"""
import sys
import os
import re
import threading
from time import sleep
import argparse
import configparser
import logging
from logging.handlers import RotatingFileHandler
from ssl import CertificateError
import requests
try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from netmiko import ConnectHandler

# Default Config File Location
config_file = '/etc/nsj.ini'
alt_config = './nsj.ini'

ERROR_PATTERN = "%%%failed%%%"
debug = 0

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(prog='nsj',
                                 description='Send Jobs to Devices based on NetGrph Inventory')

parser.add_argument("-model", metavar="regex",
                    help="Filter Devices based on Model Regex",
                    type=str)
parser.add_argument("-group", metavar="group[,group]",
                    help="Filter Devices based on Group[s]",
                    type=str)
parser.add_argument("-platform", metavar="platform",
                    help="Filter Devices based on Platform",
                    type=str)
parser.add_argument("-name", metavar="regex",
                    help="Filter Devices based on Hostname Regex",
                    type=str)
parser.add_argument("-version", metavar="regex",
                    help="Filter Devices based on Version",
                    type=str)
parser.add_argument("-scmd", metavar='cmd[,cmd]',
                    help="Send Show Commands To Devices",
                    type=str)
parser.add_argument("-cfile", metavar='CMD File',
                    help="Send Configuration File Commands",
                    type=str)
parser.add_argument("-ccmd", metavar='cmd[,cmd]',
                    help="Send Config Commands To Devices",
                    type=str)
parser.add_argument("-logd", metavar='directory',
                    help="Log per device to this directory",
                    type=str)
parser.add_argument('--timing',
                    help="Don't prompt check commands, just wait",
                    action="store_true")
parser.add_argument('--wrmem',
                    help="Save Config to NVRAM",
                    action="store_true")
parser.add_argument("--conf", metavar='file', help="Alternate Config File", type=str)
parser.add_argument("--debug", help="Set debugging level", type=int)
parser.add_argument("--verbose", help="Verbose Output", action="store_true")

args = parser.parse_args()

def get_devs():
    """Get All Devices via API"""

    url = config['api']['url'] + 'devs'
    user = config['api']['user']
    passwd = config['api']['pass']
    verify = config['api']['pass']

    if verify != '0':
        verify = True
    else:
        verify = False

    try:
        r = requests.get(url, auth=(user, passwd), verify=verify)
        if r.status_code == 200:
            return r.json()
        else:
            print("API Request Error:", r.status_code, r.text)
            raise Exception("API Failure")
    except CertificateError as e:
        print("SSL Certificate Error:", e)
        sys.exit(1)
    except requests.exceptions.SSLError as e:
        print("SSL Certificate Error:", e)
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print("Failed to Connect to API Server:", url, e)
        sys.exit(1)

def filter_devs():
    """Filter devices based on flags"""

    fdevs = get_devs()
    ndevs = []
    groups = str(args.group).split(',')

    for d in fdevs['data']:
        add = True
        if args.model and not re.search(args.model, d['Model']):
            add = False
        if args.name and not re.search(args.name, d['Name']):
            add = False
        if args.group and d['MGMT Group'] not in groups:
            add = False
        if args.platform and d['Platform'] != str(args.platform):
            add = False
        if args.version and not re.search(args.version, d['Version']):
            add = False
        if add:
            ndevs.append(d)

    return ndevs

def ssh_conn(**kwargs):
    """SSH to Device and send commands (Threaded)"""
    output_q = kwargs['output_q']
    sout = []
    try:
        net_connect = ConnectHandler(device_type=kwargs['Platform'],
                                     ip=kwargs['FQDN'],
                                     username=config['nsj']['username'],
                                     password=config['nsj']['password'])
        net_connect.enable()
        for s in kwargs['shcmds']:
            output = net_connect.send_command(s)
            #print(output)
            #output = net_connect.send_config_set(cfg_command)
            sout.append(output)
        if len(kwargs['confcmds']) > 0:
            net_connect.config_mode()
            for c in kwargs['confcmds']:
                logging.debug('Sending Command to %s: %s' % (kwargs['Name'], c))
                if args.timing:
                    output = net_connect.send_command_timing(c)
                else:
                    output = net_connect.send_command(c)
                sout.append(output)
            net_connect.exit_config_mode()
        if args.wrmem:
            logging.info("Writing Mem on %s" % (kwargs['Name']))
            net_connect.send_command("wr")
            sleep(20)
        net_connect.disconnect()
    except Exception:
        output = ERROR_PATTERN
    output_q.put({kwargs['Name']: sout})


def send_job(dl):
    """Send Commands to Devices"""

    #start_time = datetime.now()

    output_q = Queue()

    confcmds = []
    shcmds = []
    if args.scmd:
        shcmds = args.scmd.split(',')
    if args.cfile:
        cf = open(args.cfile, 'r')
        for l in cf:
            l = l.strip()
            confcmds.append(l)
    if debug > 1:
        print("CONF", confcmds)

    for d in dl:
        logging.debug("Active Threads: %s" %(str(threading.activeCount())))
        while threading.activeCount() >= int(config['nsj']['threads']):
            sleep(0.25)

        d['shcmds'] = shcmds
        d['confcmds'] = confcmds
        d['output_q'] = output_q

        my_thread = threading.Thread(target=ssh_conn, kwargs=d)
        my_thread.start()

    # Make sure all threads have finished
    main_thread = threading.currentThread()
    for some_thread in threading.enumerate():
        if some_thread != main_thread:
            some_thread.join()
    # Write Output
            ol = open(outlog, 'w')
    while not output_q.empty():
        oq = output_q.get()
        for k in oq:
            logging.info('Completed Job on %s' % (k))

            ol.write('\n\n---===[ Results from %s ]===---\n' % (k))
            for l in oq[k]:
                #l = l.strip()
                ol.write(l)
    print("Job Complete.")


def send_devs():
    """Send Show and/or Config Commands to these devices"""

    devs = filter_devs()

    if len(devs) > 0:
        print("Found " + str(len(devs)) + " Devices to send commands to:")
        for d in devs:
            print("Switch: {}, Group: {}, Model: {}, Platform: {}, Version: {}".format(
                d['Name'], d['MGMT Group'], d['Model'], d['Platform'], d['Version']))
        if query_yes_no("Send Commands to These Devices?", default="no"):
            send_job(devs)
        else:
            print("Aborting...")
    else:
        print("Could not find any devices based on filters to send job to")


def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


# Alternate Config File
if args.conf:
    config_file = args.conf

# Test configuration exists
if not os.path.exists(config_file):
    if not os.path.exists(alt_config):
        raise Exception("Configuration File not found", config_file)
    else:
        config_file = alt_config

config = configparser.ConfigParser()
config.read(config_file)

# verbose
if args.verbose:
    debug = 1

# debug
if args.debug:
    debug = args.debug
elif 'debug' in config['nsj'] and int(config['nsj']['debug']) != '0':
    debug = int(config['nsj']['debug'])

# Logging Configuration, default level INFO
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
lformat = logging.Formatter('%(asctime)s %(name)s:%(levelname)s: %(message)s')

# Debug mode Enabled
if debug > 2:
    logger.setLevel(logging.DEBUG)
    logging.debug('Enabled Debug mode')

# Enable logging to file if configured
if 'runlog' in config['nsj']:
    lfh = RotatingFileHandler(config['nsj']['runlog'], maxBytes=(1048576*5), backupCount=3)
    lfh.setFormatter(lformat)
    logger.addHandler(lfh)

# STDOUT Logging defaults to Warning
if debug < 2:
    lsh = logging.StreamHandler(sys.stdout)
    lsh.setFormatter(lformat)
    if debug > 2:
        lsh.setLevel(logging.DEBUG)
    elif debug > 1:
        lsh.setLevel(logging.INFO)
    else:
        lsh.setLevel(logging.WARNING)
    logger.addHandler(lsh)
outlog = config['nsj']['outlog']

# Sendjob based on device filters
if (args.model or args.group or args.platform or args.name) \
    and (args.scmd or args.ccmd or args.cfile):
    send_devs()
else:
    parser.print_help()
    print()
