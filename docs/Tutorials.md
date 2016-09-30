
# Use Cases

NetGrph is currently being used for several types of automation within our
environment, with many more capabilities planned as we expand the application.
The pathfinding has proved useful for troubleshooting A -> B problems across
complex network topologies, in addition to making network changes on a large
scale.

Some examples of automation used in production are the modifications to specific
SVIs, such as deploying new IP helper addresses and updating ACLs. It is also
being used to modify QoS policies, VLAN trunks, as well as both discovering and
safely cleaning up network topologies such as unused VLANs and networks. These
efforts have allowed us to make changes as scale in minutes that used to take
days or more of careful planning and ad-hoc scripting.

We are currently developing a firewall automation application on top of NetGrph
to both profile devices and insert/update their firewall rules across  all
firewalls and ACLs in the path. This is accomplished via the pathfinding
functionality, and will allow us to scale our security automation and
micro-segmentation efforts. L4 pathfinding queries can return all the L4 network
policies between any two points in under 150ms in our environment, allowing
automated security incident response, as well as rapid provisioning of new
security policies.

# Pathfinding Examples

### L2-L4 Traversal on the same switch, different VRF (details omitted)
```
$ ./netgrph.py -p 10.26.72.142 10.34.72.24

┌─[ PATHs L2-L4 ]
│
├── L2 Path : abc7t1sw1 (Gi2/42) -> abc7t1sw1 (Gi1/38)
├── L3 Path : 10.26.72.0/22 -> 10.34.72.0/22
├── L4 Path : VRF:default -> FwutilFW -> VRF:utility
├── Lx Path : 10.26.72.142 -> 10.34.72.24
├── Traversal Type : All Paths
│
├─────[ SRC 10.26.72.142 04bd.88cb.xxxx abc7t1sw1(Gi2/42) [vid:260] ]
│
├───┬─[ L2-PATH abc7t1sw1 -> abcmdf1|abcmdf2 ]
│   │
│   ├─────[ L2-HOP #1 abc7t1sw1(Te5/1) -> abcmdf1(Eth1/8) [pc:1->108] ]
│   │
│   └─────[ L2-HOP #1 abc7t1sw1(Te6/1) -> abcmdf2(Eth1/8) [pc:1->108] ]
│
├─────[ L3GW 10.26.72.0/22 abcmdf1|abcmdf2 ]
│
├───┬─[ L3-PATH 10.26.72.0/22 -> 10.25.11.0/24 ]
│   │
│   ├───┬─[ L3-HOP #1 abcmdf1(10.23.74.11) -> core1(10.23.74.10) [vid:2074] ]
│   │   │
│   │   └─────[ L2-HOP #1 abcmdf1(Eth2/26) -> core1(Eth7/27) ]
│   │
│   ├───┬─[ L3-HOP #1 abcmdf1(10.23.74.21) -> core2(10.23.74.20) [vid:3074] ]
│   │   │
│   │   └─────[ L2-HOP #1 abcmdf1(Eth3/8) -> core2(Eth4/25) ]
│   │
│   ├───┬─[ L3-HOP #1 abcmdf2(10.23.78.11) -> core1(10.23.78.10) [vid:2078] ]
│   │   │
│   │   └─────[ L2-HOP #1 abcmdf2(Eth2/26) -> core1(Eth8/25) ]
│   │
│   └───┬─[ L3-HOP #1 abcmdf2(10.23.78.21) -> core2(10.23.78.20) [vid:3078] ]
│       │
│       └─────[ L2-HOP #1 abcmdf2(Eth3/8) -> core2(Eth8/25) ]
│
├─────[ L4GW 10.25.11.0/24 [rtr: vid:1601 vrf:default] ]
│
├─────[ L4FW FwutilFW ]
│
├─────[ L4GW 10.25.12.0/24 [rtr: vid:1602 vrf:utility] ]
│
├───┬─[ L3-PATH 10.25.12.0/24 -> 10.34.72.0/22 ]
│   │
│   ├───┬─[ L3-HOP #1 core1(10.23.74.10) -> abcmdf1(10.23.74.11) [vid:2461] ]
│   │   │
│   │   └─────[ L2-HOP #1 core1(Eth7/27) -> abcmdf1(Eth2/26) ]
│   │
│   ├───┬─[ L3-HOP #1 core1(10.23.78.10) -> abcmdf2(10.23.78.11) [vid:2462] ]
│   │   │
│   │   └─────[ L2-HOP #1 core1(Eth8/25) -> abcmdf2(Eth2/26) ]
│   │
│   ├───┬─[ L3-HOP #1 core2(10.23.74.20) -> abcmdf1(10.23.74.21) [vid:3461] ]
│   │   │
│   │   └─────[ L2-HOP #1 core2(Eth4/25) -> abcmdf1(Eth3/8) ]
│   │
│   └───┬─[ L3-HOP #1 core2(10.23.78.20) -> abcmdf2(10.23.78.21) [vid:3462] ]
│       │
│       └─────[ L2-HOP #1 core2(Eth8/25) -> abcmdf2(Eth3/8) ]
│
├─────[ L3GW 10.34.72.0/22 abcmdf1|abcmdf2 ]
│
├───┬─[ L2-PATH abcmdf1|abcmdf2 -> abc7t1sw1 ]
│   │
│   ├─────[ L2-HOP #1 abcmdf1(Eth1/8) -> abc7t1sw1(Te5/1) [pc:108->1] ]
│   │
│   └─────[ L2-HOP #1 abcmdf2(Eth1/8) -> abc7t1sw1(Te6/1) [pc:108->1] ]
│
└─────[ DST 10.34.72.24 000a.b004.xxxx abc7t1sw1(Gi1/38) [vid:340] ]
```

### Discovering all equal Switched Paths as CSV between servchas. -> spp2.*
```
$ netgrph -sp servchas. spp2.* -o csv
ChildPort,ChildSwitch,Name,ParentPort,ParentSwitch,_type,distance
Te3/1,servchas1,Link,Eth7/25,core1,SPATH,0
Te1/4,servchas2,Link,Eth8/31,core1,SPATH,0
{...}
```

More Pathfinding Examples
------

Learn more about [NetGrph Pathfinding Here](PathSample.md)

# Device and IP Queries

### IP Search on the most specific CIDR (optional NetDB data included)
```
$ netgrph -ip 10.32.1.1

┌─[ Parent IP Object ]
│
│
├───┬─[ CIDR 10.32.0.0/17 ]
│   ├── Broadcast : 10.32.127.255
│   ├── Description : wireless-GUEST
│   ├── Gateway : 10.32.0.50
│   ├── IP : 10.32.1.1
│   ├── Location : MDC
│   ├── Netmask : 255.255.128.0
│   ├── Role : wireless-guest
│   ├── Router : servchas1
│   ├── Security Level : 10
│   ├── Size : 32766 nodes
│   ├── StandbyRouter : servchas2
│   ├── VLAN : 641
│   ├── VRF : guest
│   └── vrfcidr : guest-10.32.0.0/17
│
└───┬─[ NetDB IP ]
    ├── FQDN : Bhop.guest.musc.edu
    ├── MAC : 48d7.058b.1234
    ├── Switch : mdc-aruba-local1
    ├── SwitchPort : ap-1-outside
    ├── UserID : None
    ├── firstSeen : 2016-07-01 09:50:43
    ├── lastSeen : 2016-07-01 10:10:45
    └── vendor : Apple, Inc.
```

### Report on a Network Device
```
$ netgrph abc4mdf
┌─[ Device abc4mdf ]
│
├── Child Neighbors : 5
├── Distance : 1
├── MGMT Group : ABC
├── Network Count : 11
├── Parent Neighbors : 2
├── Total Neighbors : 7
├── VLAN Count : 9
├── VLAN Range : 1-1999
├── VRFs : ['default', 'guest', 'perim', 'utility']
│
├───┬─[ NEI Parents abc4mdf ]
│   │
│   ├───┬─[ core1 ]
│   │   ├── Distance : 0
│   │   ├── MGMT Group : Core
│   │   ├── child_port : Gi1/0/28
│   │   ├── child_switch : abc4mdf
│   │   ├── parent_port : Eth10/16
│   │   └── parent_switch : core1
│   │
│   └───┬─[ core2 ]
│       ├── Distance : 0
│       ├── MGMT Group : Core
│       ├── child_port : Gi2/0/28
│       ├── child_switch : abc4mdf
│       ├── parent_port : Eth10/16
│       └── parent_switch : core2
│
├───┬─[ Networks abc4mdf ]
│   │
│   ├───┬─[ CIDR 10.4.108.0/24 ]
│   │   ├── Broadcast : 10.4.108.255
│   │   ├── Description : None
│   │   ├── Gateway : 10.4.108.1
│   │   ├── Location : Unknown
│   │   ├── Netmask : 255.255.255.0
│   │   ├── Role : None
│   │   ├── Router : abc4mdf
│   │   ├── Security Level : 100
│   │   ├── Size : 254 nodes
│   │   ├── VLAN : 1
│   │   ├── VRF : default
│   │   └── vrfcidr : default-10.4.108.0/24
{...}
├───┬─[ VLANs abc4mdf ]
│   │
│   ├───┬─[ ABC-108 ]
│   │   └── Description : Abc
│   │
│   ├───┬─[ ABC-120 ]
│   │   └── Description : Abc2
│   │
│   ├───┬─[ ABC-260 ]
│   │   └── Description : utility
│   │
│   ├───┬─[ ABC-280 ]
│   │   └── Description : Printers
│   │
│   ├───┬─[ ABC-340 ]
│   │   └── Description : SECURE-UTILITY
│   │
│   ├───┬─[ ABC-408 ]
│   │   └── Description : abc-v108-voice
│   │
│   ├───┬─[ ABC-420 ]
│   │   └── Description : abc-v120-voice
│   │
│   ├───┬─[ ABC-499 ]
│   │   └── Description : abc-utility-voice
│   │
│   └───┬─[ ABC-1246 ]
│       └── Description : vendor-span

```

# L2 Queries

### L2 VLAN (Includes all bridge domains as a tree from the root)
```
$ netgrph -vid 1246

[VLAN Core-1246]
|
|--> Description : SPAN-1246
|--> Root : core1
|--> Switch Count : 2
|--> Switches : ['core2', 'core1']
|--> VLAN ID : 1246
|--> localroot : core1
|--> localstp : 20480
|
|-->[VLAN ECL-1246]
|   |--> Description : SPAN-1246
|   |--> Switch Count : 2
|   |--> Switches : ['ecl4mdf', 'ecl2e1sw1']
|   |--> localstp : 32768
{...}
```

### VLAN Database on a range for a switch group
```
$ netgrph -group ECL -vr 200-1400
Total: 4

VID             Name            Sw/Macs/Ports  Root       Switches
------------------------------------------------------------------------------------------------
 260 : utility                    6/101/109    ecl4mdf    ecl4sw1 ecl437sw2 ecl437sw1 ecl2sw1..
 408 : ecl-v108-voice             6/8/0        ecl4mdf    ecl4sw1 ecl437sw2 ecl437sw1 ecl2sw1..
 420 : ecl-v120-voice             6/2/0        ecl4mdf    ecl4sw1 ecl437sw2 ecl437sw1 ecl2sw1..
1246 : SPAN-1246                  2/1/1        core1      ecl4mdf ecl2e1sw1
```

# L3/L4 Network Queries

### Filtered Networks as JSON output (Guest CIDRs in this case)
```
netgrph -nlist guest -o JSON
{
  "Count": 109,
  "Filter": "wireless-guest:all guest:all",
  "Group": "guest",
  "Name": "Networks",
  "_ccount": 109,
  "_child105": {
    "CIDR": "10.32.0.0/17",
    "Description": "wireless-GUEST",
    "Gateway": "10.32.0.50",
    "Location": "None",
    "Name": "10.32.0.0/17",
    "NetRole": "wireless-guest",
    "Router": "servchas2",
    "SecurityLevel": "10",
    "VLAN": "641",
    "VRF": "guest",
    "_type": "CIDR"
  },
```

### L4 Security Path
```
$ netgrph -fp 10.170.16.1 8.8.8.8

Security Path: 10.170.16.0/24 --> VRF:flex --> PerimeterFW --> VRF:perim -->
               ExternalFW --> VRF:outside --> 0.0.0.0/0

PerimeterFW Logs (15min): [firewall logs link]

ExternalFW Logs (15min): [firewall logs link]
```

