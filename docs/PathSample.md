# Universal Pathfinding (L2-L4) with NetGrph
* Results are always subsecond 
* Will work across any paths less than 20 hops per segment
* Encapsulation/ordering needs more work
* [NetGrph Link](https://github.com/yantisj/netgrph)


### Example 1: L2 -> L2 : Path between two devices on the same Switch/VLAN
```
$ ./netgrph.py -p 10.26.72.142 10.26.73.17
┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art7t1sw1 (Gi4/2)
│
└───┬─[ L2PATH 10.26.72.142 -> 10.26.73.17 ]
    │
    ├───┬─[ CIDR 10.26.72.0/22 ]
    │   ├── Broadcast : 10.26.75.255
    │   ├── Description : ART-UTILITY
    │   ├── Gateway : 10.26.72.50
    │   ├── IP : 10.26.72.142
    │   ├── Location :  ART-DC
    │   ├── Netmask : 255.255.252.0
    │   ├── Role : utility
    │   ├── Router : artmdf1
    │   ├── Security Level : 100
    │   ├── Size : 1022 nodes
    │   ├── StandbyRouter : artmdf2
    │   ├── VLAN : 260
    │   ├── VRF : default
    │   └── vrfcidr : default-10.26.72.0/22
    │
    ├───┬─[ NetDB 10.26.72.142 ]
    │   ├── FQDN : art7035-nw-ap1.xxxx
    │   ├── MAC : 04bd.88cb.xxxx
    │   ├── Switch : art7t1sw1
    │   ├── SwitchPort : Gi2/42
    │   ├── UserID : utility-vlan
    │   ├── VLAN : 260
    │   ├── firstSeen : 2015-10-22 10:33:11
    │   ├── lastSeen : 2016-08-20 17:15:43
    │   └── vendor : Aruba Networks
    │
    └───┬─[ NetDB 10.26.73.17 ]
        ├── FQDN : art8e2-w-ap1.xxxx
        ├── MAC : 40e3.d6c5.xxxx
        ├── Switch : art7t1sw1
        ├── SwitchPort : Gi4/2
        ├── UserID : utility-vlan
        ├── VLAN : 260
        ├── firstSeen : 2016-03-18 15:14:36
        ├── lastSeen : 2016-08-20 17:15:43
        └── vendor : Aruba Networks
```

### Example 1 L2 -> L3 -> L2: Path between two devices on the same Switch, different VLAN
```
$ ./netgrph.py -p 10.26.72.142 10.28.7.137
┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art7t1sw1 (Gi9/47)
├── L3 Path : 10.26.72.142 -> 10.28.7.137
│
├───┬─[ SRC 10.26.72.142 ]
│   │
│   ├───┬─[ CIDR 10.26.72.0/22 ]
│   │   ├── Broadcast : 10.26.75.255
│   │   ├── Description : ART-UTILITY
│   │   ├── Gateway : 10.26.72.50
│   │   ├── IP : 10.26.72.142
│   │   ├── Location :  ART-DC
│   │   ├── Netmask : 255.255.252.0
│   │   ├── Role : utility
│   │   ├── Router : artmdf1
│   │   ├── Security Level : 100
│   │   ├── Size : 1022 nodes
│   │   ├── StandbyRouter : artmdf2
│   │   ├── VLAN : 260
│   │   ├── VRF : default
│   │   └── vrfcidr : default-10.26.72.0/22
│   │
│   └───┬─[ NetDB 10.26.72.142 ]
│       ├── FQDN : art7035-nw-ap1.xxxx
│       ├── MAC : 04bd.88cb.xxxx
│       ├── Switch : art7t1sw1
│       ├── SwitchPort : Gi2/42
│       ├── UserID : utility-vlan
│       ├── VLAN : 260
│       ├── firstSeen : 2015-10-22 10:33:11
│       ├── lastSeen : 2016-08-20 16:50:43
│       └── vendor : Aruba Networks
│
├───┬─[ L2-PATH art7t1sw1 -> artmdf1|artmdf2 ]
│   ├── Distance : 0
│   ├── Links : 2
│   │
│   ├───┬─[ L2-PATH artmdf1(Eth1/8) <-> art7t1sw1(Te5/1) ]
│   │   ├── Child Channel : 1
│   │   ├── Child Port : Te5/1
│   │   ├── Child Switch : art7t1sw1
│   │   ├── Link VLANs : 1-1005
│   │   ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│   │   ├── Native VLAN : 1
│   │   ├── Parent Channel : 108
│   │   ├── Parent Port : Eth1/8
│   │   ├── Parent Switch : artmdf1
│   │   └── distance : 0
│   │
│   └───┬─[ L2-PATH artmdf2(Eth1/8) <-> art7t1sw1(Te6/1) ]
│       ├── Child Channel : 1
│       ├── Child Port : Te6/1
│       ├── Child Switch : art7t1sw1
│       ├── Link VLANs : 1-1005
│       ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│       ├── Native VLAN : 1
│       ├── Parent Channel : 108
│       ├── Parent Port : Eth1/8
│       ├── Parent Switch : artmdf2
│       └── distance : 0
│
├───┬─[ L2-PATH artmdf1|artmdf2 -> art7t1sw1 ]
│   ├── Distance : 1
│   ├── Links : 2
│   │
│   ├───┬─[ L2-PATH artmdf1(Eth1/8) <-> art7t1sw1(Te5/1) ]
│   │   ├── Child Channel : 1
│   │   ├── Child Port : Te5/1
│   │   ├── Child Switch : art7t1sw1
│   │   ├── Link VLANs : 1-1005
│   │   ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│   │   ├── Native VLAN : 1
│   │   ├── Parent Channel : 108
│   │   ├── Parent Port : Eth1/8
│   │   ├── Parent Switch : artmdf1
│   │   └── distance : 1
│   │
│   └───┬─[ L2-PATH artmdf2(Eth1/8) <-> art7t1sw1(Te6/1) ]
│       ├── Child Channel : 1
│       ├── Child Port : Te6/1
│       ├── Child Switch : art7t1sw1
│       ├── Link VLANs : 1-1005
│       ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│       ├── Native VLAN : 1
│       ├── Parent Channel : 108
│       ├── Parent Port : Eth1/8
│       ├── Parent Switch : artmdf2
│       └── distance : 1
│
└───┬─[ DST 10.28.7.137 ]
    │
    ├───┬─[ CIDR 10.28.4.0/22 ]
    │   ├── Broadcast : 10.28.7.255
    │   ├── Description : ART-Printers
    │   ├── Gateway : 10.28.4.50
    │   ├── IP : 10.28.7.137
    │   ├── Location :  ART-DC
    │   ├── Netmask : 255.255.252.0
    │   ├── Role : printer
    │   ├── Router : artmdf1
    │   ├── Security Level : 100
    │   ├── Size : 1022 nodes
    │   ├── StandbyRouter : artmdf2
    │   ├── VLAN : 280
    │   ├── VRF : default
    │   └── vrfcidr : default-10.28.4.0/22
    │
    └───┬─[ NetDB 10.28.7.137 ]
        ├── FQDN : HPF784CA.xxxx
        ├── MAC : ecb1.d7f7.xxxx
        ├── Switch : art7t1sw1
        ├── SwitchPort : Gi9/47
        ├── UserID : nac-fe
        ├── VLAN : 280
        ├── firstSeen : 2015-11-10 11:23:26
        ├── lastSeen : 2016-08-20 16:50:43
        └── vendor : Hewlett Packard
```

## Example 3: L2 -> L3 -> L4 -> L3 -> L2: Path between two devices on the same Switch, different VRF
```
$ ./netgrph.py -p 10.26.72.142 10.34.72.24

┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art7t1sw1 (Gi1/38)
├── L3 Path : 10.26.72.142 -> 10.34.72.24
├── L4 Path : 10.26.72.0/22 -> VRF:default -> FwutilFW -> VRF:utility -> 10.34.72.0/22
│
├───┬─[ SRC 10.26.72.142 ]
│   │
│   ├───┬─[ CIDR 10.26.72.0/22 ]
│   │   ├── Broadcast : 10.26.75.255
│   │   ├── Description : ART-UTILITY
│   │   ├── Gateway : 10.26.72.50
│   │   ├── IP : 10.26.72.142
│   │   ├── Location :  ART-DC
│   │   ├── Netmask : 255.255.252.0
│   │   ├── Role : utility
│   │   ├── Router : artmdf1
│   │   ├── Security Level : 100
│   │   ├── Size : 1022 nodes
│   │   ├── StandbyRouter : artmdf2
│   │   ├── VLAN : 260
│   │   ├── VRF : default
│   │   └── vrfcidr : default-10.26.72.0/22
│   │
│   └───┬─[ NetDB 10.26.72.142 ]
│       ├── FQDN : art7035-nw-ap1.xxxx
│       ├── MAC : 04bd.88cb.xxxx
│       ├── Switch : art7t1sw1
│       ├── SwitchPort : Gi2/42
│       ├── UserID : utility-vlan
│       ├── VLAN : 260
│       ├── firstSeen : 2015-10-22 10:33:11
│       ├── lastSeen : 2016-08-20 16:55:46
│       └── vendor : Aruba Networks
│
├───┬─[ L2-PATH art7t1sw1 -> artmdf1|artmdf2 ]
│   ├── Distance : 0
│   ├── Links : 2
│   │
│   ├───┬─[ L2-PATH artmdf1(Eth1/8) <-> art7t1sw1(Te5/1) ]
│   │   ├── Child Channel : 1
│   │   ├── Child Port : Te5/1
│   │   ├── Child Switch : art7t1sw1
│   │   ├── Link VLANs : 1-1005
│   │   ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│   │   ├── Native VLAN : 1
│   │   ├── Parent Channel : 108
│   │   ├── Parent Port : Eth1/8
│   │   ├── Parent Switch : artmdf1
│   │   └── distance : 0
│   │
│   └───┬─[ L2-PATH artmdf2(Eth1/8) <-> art7t1sw1(Te6/1) ]
│       ├── Child Channel : 1
│       ├── Child Port : Te6/1
│       ├── Child Switch : art7t1sw1
│       ├── Link VLANs : 1-1005
│       ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│       ├── Native VLAN : 1
│       ├── Parent Channel : 108
│       ├── Parent Port : Eth1/8
│       ├── Parent Switch : artmdf2
│       └── distance : 0
│
├───┬─[ L4-PATH 10.26.72.0/22 -> VRF:default -> FwutilFW -> VRF:utility -> 10.34.72.0/22 ]
│   │
│   ├───┬─[ L3-PATH 10.26.72.0/22 -> 10.25.11.0/24 ]
│   │   ├── Hops : 4
│   │   ├── Max Hops : 1
│   │   ├── Path : 10.26.72.0/22 -> 10.25.11.0/24
│   │   ├── VRF : default
│   │   │
│   │   ├───┬─[ L3-HOP Hop ]
│   │   │   ├── From IP : 10.23.74.11
│   │   │   ├── From Router : artmdf1
│   │   │   ├── To IP : 10.23.74.10
│   │   │   ├── To Router : core1
│   │   │   └── distance : 1
│   │   │
│   │   ├───┬─[ L3-HOP Hop ]
│   │   │   ├── From IP : 10.23.74.21
│   │   │   ├── From Router : artmdf1
│   │   │   ├── To IP : 10.23.74.20
│   │   │   ├── To Router : core2
│   │   │   └── distance : 1
│   │   │
│   │   ├───┬─[ L3-HOP Hop ]
│   │   │   ├── From IP : 10.23.78.11
│   │   │   ├── From Router : artmdf2
│   │   │   ├── To IP : 10.23.78.10
│   │   │   ├── To Router : core1
│   │   │   └── distance : 1
│   │   │
│   │   └───┬─[ L3-HOP Hop ]
│   │       ├── From IP : 10.23.78.21
│   │       ├── From Router : artmdf2
│   │       ├── To IP : 10.23.78.20
│   │       ├── To Router : core2
│   │       └── distance : 1
│   │
│   ├───┬─[ L4-HOP Network ]
│   │   ├── cidr : 10.25.11.0/24
│   │   ├── desc : None
│   │   ├── gateway : 10.25.11.50
│   │   ├── name : default-10.25.11.0/24
│   │   ├── time : 2016-08-20 16:36:31.480491
│   │   ├── vid : 1601
│   │   ├── vrf : default
│   │   └── vrfcidr : default-10.25.11.0/24
│   │
│   ├───┬─[ L4-HOP FW ]
│   │   ├── hostname : fsm-fwutil
│   │   ├── logIndex : firewalls
│   │   ├── name : FwutilFW
│   │   └── time : 2016-08-20 10:24:26.012424
│   │
│   ├───┬─[ L4-HOP Network ]
│   │   ├── cidr : 10.25.12.0/24
│   │   ├── desc : None
│   │   ├── gateway : 10.25.12.50
│   │   ├── name : utility-10.25.12.0/24
│   │   ├── time : 2016-08-20 16:36:31.490825
│   │   ├── vid : 1602
│   │   ├── vrf : utility
│   │   └── vrfcidr : utility-10.25.12.0/24
│   │
│   └───┬─[ L3-PATH 10.25.12.0/24 -> 10.34.72.0/22 ]
│       ├── Hops : 4
│       ├── Max Hops : 1
│       ├── Path : 10.25.12.0/24 -> 10.34.72.0/22
│       ├── VRF : utility
│       │
│       ├───┬─[ L3-HOP Hop ]
│       │   ├── From IP : 10.23.74.10
│       │   ├── From Router : core1
│       │   ├── To IP : 10.23.74.11
│       │   ├── To Router : artmdf1
│       │   └── distance : 1
│       │
│       ├───┬─[ L3-HOP Hop ]
│       │   ├── From IP : 10.23.78.10
│       │   ├── From Router : core1
│       │   ├── To IP : 10.23.78.11
│       │   ├── To Router : artmdf2
│       │   └── distance : 1
│       │
│       ├───┬─[ L3-HOP Hop ]
│       │   ├── From IP : 10.23.74.20
│       │   ├── From Router : core2
│       │   ├── To IP : 10.23.74.21
│       │   ├── To Router : artmdf1
│       │   └── distance : 1
│       │
│       └───┬─[ L3-HOP Hop ]
│           ├── From IP : 10.23.78.20
│           ├── From Router : core2
│           ├── To IP : 10.23.78.21
│           ├── To Router : artmdf2
│           └── distance : 1
│
├───┬─[ L2-PATH artmdf1|artmdf2 -> art7t1sw1 ]
│   ├── Distance : 1
│   ├── Links : 2
│   │
│   ├───┬─[ L2-PATH artmdf1(Eth1/8) <-> art7t1sw1(Te5/1) ]
│   │   ├── Child Channel : 1
│   │   ├── Child Port : Te5/1
│   │   ├── Child Switch : art7t1sw1
│   │   ├── Link VLANs : 1-1005
│   │   ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│   │   ├── Native VLAN : 1
│   │   ├── Parent Channel : 108
│   │   ├── Parent Port : Eth1/8
│   │   ├── Parent Switch : artmdf1
│   │   └── distance : 1
│   │
│   └───┬─[ L2-PATH artmdf2(Eth1/8) <-> art7t1sw1(Te6/1) ]
│       ├── Child Channel : 1
│       ├── Child Port : Te6/1
│       ├── Child Switch : art7t1sw1
│       ├── Link VLANs : 1-1005
│       ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│       ├── Native VLAN : 1
│       ├── Parent Channel : 108
│       ├── Parent Port : Eth1/8
│       ├── Parent Switch : artmdf2
│       └── distance : 1
│
└───┬─[ DST 10.34.72.24 ]
    │
    ├───┬─[ CIDR 10.34.72.0/22 ]
    │   ├── Broadcast : 10.34.75.255
    │   ├── Description : ART-UTILITY-SEC
    │   ├── Gateway : 10.34.72.50
    │   ├── IP : 10.34.72.24
    │   ├── Location :  ART-DC
    │   ├── Netmask : 255.255.252.0
    │   ├── Role : utility
    │   ├── Router : artmdf1
    │   ├── Security Level : 150
    │   ├── Size : 1022 nodes
    │   ├── StandbyRouter : artmdf2
    │   ├── VLAN : 340
    │   ├── VRF : utility
    │   └── vrfcidr : utility-10.34.72.0/22
    │
    └───┬─[ NetDB 10.34.72.24 ]
        ├── FQDN : 320LOYTEC01.xxxx
        ├── MAC : 000a.b004.xxxx
        ├── Switch : art7t1sw1
        ├── SwitchPort : Gi1/38
        ├── UserID : nac-jci
        ├── VLAN : 340
        ├── firstSeen : 2015-10-10 09:52:44
        ├── lastSeen : 2016-08-20 17:00:43
        └── vendor : LOYTEC electronics GmbH
```
