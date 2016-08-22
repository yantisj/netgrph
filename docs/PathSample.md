# Universal Pathfinding (L2-L4) with NetGrph
* Results are always subsecond
* Quick Paths shows full L2-L4 header summary
* Detailed Paths default to single-path, can show all paths
* Will scale across any path depth, O(N+L) complexity
* TODO: Add configuration snippets for each hop/layer
* [NetGrph Link](https://github.com/yantisj/netgrph)


### Example 1: L2 -> L2 : Quick Path between two devices on the same Switch/VLAN
```
./netgrph.py 10.26.72.142 10.26.73.17
┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art7t1sw1 (Gi4/2)
├── Traversal Type : All Paths
│
├─────[ SRC 10.26.72.142 04bd.88cb.xxxx art7t1sw1(Gi2/42) [vid:260] ]
│
└─────[ DST 10.26.72.142 40e3.d6c5.xxxx art7t1sw1(Gi4/2) [vid:260] ]
```

### Example 2: L2 -> L2 : Detailed Path between two devices on different switches, same VLAN
```
$ ./netgrph.py -all -p 10.26.72.142 10.26.73.254
┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art1t2sw1 (Gi2/0/37)
├── Traversal Type : All Paths
│
├─────[ SRC 10.26.72.142 04bd.88cb.xxxx art7t1sw1(Gi2/42) [vid:260] ]
│   ├── FQDN : art7035-nw-ap1.xxxx
│   ├── MAC : 04bd.88cb.xxxx
│   ├── Switch : art7t1sw1
│   ├── SwitchPort : Gi2/42
│   ├── UserID : utility-vlan
│   ├── VLAN : 260
│   ├── firstSeen : 2015-10-22 10:33:11
│   ├── lastSeen : 2016-08-22 10:10:44
│   └── vendor : Aruba Networks
│
├───┬─[ L2-PATH art7t1sw1 -> art1t2sw1 ]
│   ├── Distance : 2
│   ├── Links : 4
│   ├── Traversal Type : All Paths
│   │
│   ├───┬─[ L2-HOP #1 art7t1sw1(Te5/1) -> artmdf1(Eth1/8) [pc:1->108] ]
│   │   ├── From Channel : 1
│   │   ├── From Port : Te5/1
│   │   ├── From Switch : art7t1sw1
│   │   ├── Link VLANs : 1-1005
│   │   ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│   │   ├── Native VLAN : 1
│   │   ├── To Channel : 108
│   │   ├── To Port : Eth1/8
│   │   ├── To Switch : artmdf1
│   │   └── distance : 1
│   │
│   ├───┬─[ L2-HOP #1 art7t1sw1(Te6/1) -> artmdf2(Eth1/8) [pc:1->108] ]
│   │   ├── From Channel : 1
│   │   ├── From Port : Te6/1
│   │   ├── From Switch : art7t1sw1
│   │   ├── Link VLANs : 1-1005
│   │   ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│   │   ├── Native VLAN : 1
│   │   ├── To Channel : 108
│   │   ├── To Port : Eth1/8
│   │   ├── To Switch : artmdf2
│   │   └── distance : 1
│   │
│   ├───┬─[ L2-HOP #2 artmdf1(Eth1/10) -> art1t2sw1(Gi1/1/1) [pc:110->1] ]
│   │   ├── From Channel : 110
│   │   ├── From Port : Eth1/10
│   │   ├── From Switch : artmdf1
│   │   ├── Link VLANs : 1-1005,1246
│   │   ├── Link rVLANs : 1246
│   │   ├── Native VLAN : 1
│   │   ├── To Channel : 1
│   │   ├── To Port : Gi1/1/1
│   │   ├── To Switch : art1t2sw1
│   │   └── distance : 2
│   │
│   └───┬─[ L2-HOP #2 artmdf2(Eth1/10) -> art1t2sw1(Gi2/1/1) [pc:110->1] ]
│       ├── From Channel : 110
│       ├── From Port : Eth1/10
│       ├── From Switch : artmdf2
│       ├── Link VLANs : 1-1005,1246
│       ├── Link rVLANs : 1246
│       ├── Native VLAN : 1
│       ├── To Channel : 1
│       ├── To Port : Gi2/1/1
│       ├── To Switch : art1t2sw1
│       └── distance : 2
│
└─────[ DST 10.26.72.142 6cf3.7fcd.xxxx art1t2sw1(Gi2/0/37) [vid:260] ]
    ├── FQDN : art1302-c-ap1.xxxx
    ├── MAC : 6cf3.7fcd.xxxx
    ├── Switch : art1t2sw1
    ├── SwitchPort : Gi2/0/37
    ├── UserID : utility-vlan
    ├── VLAN : 260
    ├── firstSeen : 2013-06-23 20:42:53
    ├── lastSeen : 2016-08-22 10:10:44
    └── vendor : Aruba Networks
```

### Example 3: L2 -> L3 -> L2: Quick Path between two devices on the same Switch, different VLAN
```

┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art7t1sw1 (Gi9/47)
├── L3 Path : 10.26.72.0/22 -> 10.28.4.0/22
├── Lx Path : 10.26.72.142 -> 10.28.7.137
├── Traversal Type : All Paths
│
├─────[ SRC 10.26.72.142 04bd.88cb.xxxx art7t1sw1(Gi2/42) [vid:260] ]
│
├───┬─[ L2-PATH art7t1sw1 -> artmdf1|artmdf2 ]
│   │
│   ├─────[ L2-HOP #1 art7t1sw1(Te5/1) -> artmdf1(Eth1/8) [pc:1->108] ]
│   │
│   └─────[ L2-HOP #1 art7t1sw1(Te6/1) -> artmdf2(Eth1/8) [pc:1->108] ]
│
├─────[ L3GW 10.26.72.0/22 artmdf1|artmdf2 ]
│
├─────[ L3GW 10.28.4.0/22 artmdf1|artmdf2 ]
│
├───┬─[ L2-PATH artmdf1|artmdf2 -> art7t1sw1 ]
│   │
│   ├─────[ L2-HOP #1 artmdf1(Eth1/8) -> art7t1sw1(Te5/1) [pc:108->1] ]
│   │
│   └─────[ L2-HOP #1 artmdf2(Eth1/8) -> art7t1sw1(Te6/1) [pc:108->1] ]
│
└─────[ DST 10.26.72.142 ecb1.d7f7.xxxx art7t1sw1(Gi9/47) [vid:280] ]
```

### Example 4: L2 -> L4 -> L2: Quick Paths between two devices on the same Switch, different VRF
```
┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art7t1sw1 (Gi1/38)
├── L3 Path : 10.26.72.0/22 -> 10.34.72.0/22
├── L4 Path : VRF:default -> FwutilFW -> VRF:utility
├── Lx Path : 10.26.72.142 -> 10.34.72.24
├── Traversal Type : All Paths
│
├─────[ SRC 10.26.72.142 04bd.88cb.xxxx art7t1sw1(Gi2/42) ]
│
├───┬─[ L2-PATH art7t1sw1 -> artmdf1|artmdf2 ]
│   │
│   ├─────[ L2-HOP #1 art7t1sw1(Te5/1) -> artmdf1(Eth1/8) [pc:1->108] ]
│   │
│   └─────[ L2-HOP #1 art7t1sw1(Te6/1) -> artmdf2(Eth1/8) [pc:1->108] ]
│
├─────[ L3GW 10.26.72.0/22 artmdf1|artmdf2 ]
│
├───┬─[ L3-PATH 10.26.72.0/22 -> 10.25.11.0/24 ]
│   │
│   ├───┬─[ L3-HOP #1 artmdf1(10.23.74.11) -> core1(10.23.74.10) [vid:2074] ]
│   │   │
│   │   └─────[ L2-HOP #1 artmdf1(Eth2/26) -> core1(Eth7/27) ]
│   │
│   ├───┬─[ L3-HOP #1 artmdf1(10.23.74.21) -> core2(10.23.74.20) [vid:3074] ]
│   │   │
│   │   └─────[ L2-HOP #1 artmdf1(Eth3/8) -> core2(Eth4/25) ]
│   │
│   ├───┬─[ L3-HOP #1 artmdf2(10.23.78.11) -> core1(10.23.78.10) [vid:2078] ]
│   │   │
│   │   └─────[ L2-HOP #1 artmdf2(Eth2/26) -> core1(Eth8/25) ]
│   │
│   └───┬─[ L3-HOP #1 artmdf2(10.23.78.21) -> core2(10.23.78.20) [vid:3078] ]
│       │
│       └─────[ L2-HOP #1 artmdf2(Eth3/8) -> core2(Eth8/25) ]
│
├─────[ L4GW 10.25.11.0/24 [rtr: vid:1601 vrf:default] ]
│
├─────[ L4FW FwutilFW ]
│
├─────[ L4GW 10.25.12.0/24 [rtr: vid:1602 vrf:utility] ]
│
├───┬─[ L3-PATH 10.25.12.0/24 -> 10.34.72.0/22 ]
│   │
│   ├───┬─[ L3-HOP #1 core1(10.23.74.10) -> artmdf1(10.23.74.11) [vid:2461] ]
│   │   │
│   │   └─────[ L2-HOP #1 core1(Eth7/27) -> artmdf1(Eth2/26) ]
│   │
│   ├───┬─[ L3-HOP #1 core1(10.23.78.10) -> artmdf2(10.23.78.11) [vid:2462] ]
│   │   │
│   │   └─────[ L2-HOP #1 core1(Eth8/25) -> artmdf2(Eth2/26) ]
│   │
│   ├───┬─[ L3-HOP #1 core2(10.23.74.20) -> artmdf1(10.23.74.21) [vid:3461] ]
│   │   │
│   │   └─────[ L2-HOP #1 core2(Eth4/25) -> artmdf1(Eth3/8) ]
│   │
│   └───┬─[ L3-HOP #1 core2(10.23.78.20) -> artmdf2(10.23.78.21) [vid:3462] ]
│       │
│       └─────[ L2-HOP #1 core2(Eth8/25) -> artmdf2(Eth3/8) ]
│
├─────[ L3GW 10.34.72.0/22 artmdf1|artmdf2 ]
│
├───┬─[ L2-PATH artmdf1|artmdf2 -> art7t1sw1 ]
│   │
│   ├─────[ L2-HOP #1 artmdf1(Eth1/8) -> art7t1sw1(Te5/1) [pc:108->1] ]
│   │
│   └─────[ L2-HOP #1 artmdf2(Eth1/8) -> art7t1sw1(Te6/1) [pc:108->1] ]
│
└─────[ DST 10.34.72.24 000a.b004.xxxx art7t1sw1(Gi1/38) ]
```

## Example 5: L2 -> L3 -> L4 -> L3 -> L2: Single Detailed Path between two devices on the same Switch, different VRF
```
$ ./netgrph.py -p 10.26.72.142 10.34.72.24

┌─[ PATHs L2-L4 ]
│
├── L2 Path : art7t1sw1 (Gi2/42) -> art7t1sw1 (Gi1/38)
├── L3 Path : 10.26.72.0/22 -> 10.34.72.0/22
├── L4 Path : VRF:default -> FwutilFW -> VRF:utility
├── Lx Path : 10.26.72.142 -> 10.34.72.24
├── Traversal Type : Single Path
│
├───┬─[ SRC 10.26.72.142 04bd.88cb.xxxx art7t1sw1(Gi2/42) ]
│   ├── FQDN : art7035-nw-ap1.xxxx
│   ├── MAC : 04bd.88cb.xxxx
│   ├── Switch : art7t1sw1
│   ├── SwitchPort : Gi2/42
│   ├── UserID : utility-vlan
│   ├── VLAN : 260
│   ├── firstSeen : 2015-10-22 10:33:11
│   ├── lastSeen : 2016-08-22 10:15:45
│   └── vendor : Aruba Networks
│
├───┬─[ L2-PATH art7t1sw1 -> artmdf1|artmdf2 ]
│   ├── Distance : 1
│   ├── Links : 2
│   ├── Traversal Coverage : 50%
│   ├── Traversal Type : Single Path
│   │
│   └───┬─[ L2-HOP #1 art7t1sw1(Te5/1) -> artmdf1(Eth1/8) [pc:1->108] ]
│       ├── From Channel : 1
│       ├── From Port : Te5/1
│       ├── From Switch : art7t1sw1
│       ├── Link VLANs : 1-1005
│       ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│       ├── Native VLAN : 1
│       ├── To Channel : 108
│       ├── To Port : Eth1/8
│       ├── To Switch : artmdf1
│       └── distance : 1
│
├───┬─[ L3GW 10.26.72.0/22 artmdf1|artmdf2 ]
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
├───┬─[ L3-PATH 10.26.72.0/22 -> 10.25.11.0/24 ]
│   ├── Distance : 1
│   ├── Hops : 4
│   ├── Path : 10.26.72.0/22 -> 10.25.11.0/24
│   ├── Traversal Coverage : 25%
│   ├── Traversal Type : Single Path
│   ├── VRF : default
│   │
│   └───┬─[ L3-HOP #1 artmdf1(10.23.74.11) -> core1(10.23.74.10) [vid:2074] ]
│       ├── From IP : 10.23.74.11
│       ├── From Router : artmdf1
│       ├── To IP : 10.23.74.10
│       ├── To Router : core1
│       ├── VLAN : 2074
│       ├── distance : 1
│       │
│       └───┬─[ L2-HOP #1 artmdf1(Eth2/26) -> core1(Eth7/27) ]
│           ├── From Channel : 0
│           ├── From Port : Eth2/26
│           ├── From Switch : artmdf1
│           ├── Link VLANs : 1246,2074,2446-2450,2461
│           ├── Link rVLANs : 1246,2074,2446-2450,2461
│           ├── Native VLAN : 1
│           ├── To Channel : 0
│           ├── To Port : Eth7/27
│           ├── To Switch : core1
│           └── distance : 1
│
├───┬─[ L4GW 10.25.11.0/24 [rtr: vid:1601 vrf:default] ]
│   ├── cidr : 10.25.11.0/24
│   ├── desc : None
│   ├── gateway : 10.25.11.50
│   ├── name : default-10.25.11.0/24
│   ├── time : 2016-08-21 12:03:14.277146
│   ├── vid : 1601
│   ├── vrf : default
│   └── vrfcidr : default-10.25.11.0/24
│
├───┬─[ L4FW FwutilFW ]
│   ├── hostname : fsm-fwutil
│   ├── logIndex : firewalls
│   ├── name : FwutilFW
│   └── time : 2016-08-21 12:03:39.133668
│
├───┬─[ L4GW 10.25.12.0/24 [rtr: vid:1602 vrf:utility] ]
│   ├── cidr : 10.25.12.0/24
│   ├── desc : None
│   ├── gateway : 10.25.12.50
│   ├── name : utility-10.25.12.0/24
│   ├── time : 2016-08-21 12:03:14.287521
│   ├── vid : 1602
│   ├── vrf : utility
│   └── vrfcidr : utility-10.25.12.0/24
│
├───┬─[ L3-PATH 10.25.12.0/24 -> 10.34.72.0/22 ]
│   ├── Distance : 1
│   ├── Hops : 4
│   ├── Path : 10.25.12.0/24 -> 10.34.72.0/22
│   ├── Traversal Coverage : 25%
│   ├── Traversal Type : Single Path
│   ├── VRF : utility
│   │
│   └───┬─[ L3-HOP #1 core1(10.23.74.10) -> artmdf1(10.23.74.11) [vid:2461] ]
│       ├── From IP : 10.23.74.10
│       ├── From Router : core1
│       ├── To IP : 10.23.74.11
│       ├── To Router : artmdf1
│       ├── VLAN : 2461
│       ├── distance : 1
│       │
│       └───┬─[ L2-HOP #1 core1(Eth7/27) -> artmdf1(Eth2/26) ]
│           ├── From Channel : 0
│           ├── From Port : Eth7/27
│           ├── From Switch : core1
│           ├── Link VLANs : 1246,2074,2446-2450,2461
│           ├── Link rVLANs : 1246,2074,2446-2450,2461
│           ├── Native VLAN : 1
│           ├── To Channel : 0
│           ├── To Port : Eth2/26
│           ├── To Switch : artmdf1
│           └── distance : 1
│
├───┬─[ L3GW 10.34.72.0/22 ]
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
├───┬─[ L2-PATH artmdf1|artmdf2 -> art7t1sw1 ]
│   ├── Distance : 1
│   ├── Links : 2
│   ├── Traversal Coverage : 50%
│   ├── Traversal Type : Single Path
│   │
│   └───┬─[ L2-HOP #1 artmdf1(Eth1/8) -> art7t1sw1(Te5/1) [pc:108->1] ]
│       ├── From Channel : 108
│       ├── From Port : Eth1/8
│       ├── From Switch : artmdf1
│       ├── Link VLANs : 1-1005
│       ├── Link rVLANs : 50,70,72,74,76,78,130,220,260,270-272,277,280,300,310,340,470,472,474,476,478,826
│       ├── Native VLAN : 1
│       ├── To Channel : 1
│       ├── To Port : Te5/1
│       ├── To Switch : art7t1sw1
│       └── distance : 1
│
└───┬─[ DST 10.34.72.24 000a.b004.xxxx art7t1sw1(Gi1/38) ]
    ├── FQDN : 320LOYTEC01.xxxx
    ├── MAC : 000a.b004.xxxx
    ├── Switch : art7t1sw1
    ├── SwitchPort : Gi1/38
    ├── UserID : nac-xxx
    ├── VLAN : 340
    ├── firstSeen : 2015-10-10 09:52:44
    ├── lastSeen : 2016-08-22 10:15:45
    └── vendor : LOYTEC electronics GmbH
```
