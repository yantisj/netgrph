#!/usr/bin/env python3
""" Test Random IP's for errors"""
import subprocess

ip1 = open('/tmp/ip1.txt', 'r')
ip2 = open('/tmp/ip2.txt', 'r')

verbose = True

for e1, e2 in zip(ip1, ip2):
    e1 = e1.strip()
    e2 = e2.strip()
    #print(e1, e2)

    cmd = './netgrph.py ' + e1 + ' ' + e2

    proc = subprocess.Popen(
        [cmd],
        stdout=subprocess.PIPE,
        shell=True,
        universal_newlines=True)

    (out, err) = proc.communicate()

    if err:
        print(cmd, err)
    elif out and verbose:
        print(out)
