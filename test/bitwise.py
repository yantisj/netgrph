#!/usr/bin/env python
import sys
import ipaddress


def int_to_bin(num, bits=32):
    r = ''
    while bits:
        r = ('1' if num&1 else '0') + r
        bits = bits - 1
        num = num >> 1
    print(r)


myip = sys.argv[1]


ip = ipaddress.IPv4Address(myip)
i = int.from_bytes(ip.packed, byteorder='big')

print(ip.packed)
print(i)
int_to_bin(i)

