## Synopsis

NetGrph models ethernet networks in the [Neo4j](http://neo4j.com) Graph
Database. The model enables you to navigate your LAN/WAN as paths of
interconnected nodes and relationships in software, enabling automation and
troubleshooting across the network instead of box by box.

NetGrph can perform universal L2/L3/L4 path traversals, providing context for
each layer along the path. It also serves as a VLAN and subnet database, showing
how everything is related. It should scale well on even the largest networks,
allowing sub-second queries across thousands of network devices. This enables
the mapping of complex network relationships for discovery and automation.

Data from queries can be returned as CSV, JSON, YAML, or Ascii tree-art. Network
Visualizations can be created by querying the Neo4j webapp as shown below. The
data model should translate for use with tools such as D3.js, vis.js or Graphwiz
via both the native Neo4j API as well as NetGrph's tree data structure.

## Data Model
### Discovering the Routed SVI Paths from Vlan 110 to 200
![vlan110](https://dl.dropboxusercontent.com/u/73454/svipath2.svg)


[L3 SVIs: Yellow] [L2 VLANs: Green] [Switches/Routers: Blue]
<br>
<br>

### Discovering the Security Path from Vlan 696 --> 641 across multiple L2/L3 Firewalls
![fwpath](https://dl.dropboxusercontent.com/u/73454/security-path2.svg)


[Networks: Yellow] [VRFs: Green] [Firewalls: Blue]

<br>

### Neighbor Tree from the Core out to a distance of 3

<img src="https://dl.dropboxusercontent.com/u/73454/network-graph.svg" alt="NEI Tree" width="800" height="800">



<br>

## Program Example

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

### More Universal Path Examples

See [Traversal Details](docs/PathSample.md)

### Query Options
```

usage: netgrph [-h] [-ip] [-net] [-nlist] [-dev] [-fpath src] [-rpath src]
               [-spath src] [-group] [-vrange 1[-4096]] [-vid] [-vtree]
               [-output TREE] [--conf file] [--debug DEBUG] [--verbose]
               search

Query the NetGrph Database

positional arguments:
  search            Search the NetGrph Database (Wildcard Default)

optional arguments:
  -h, --help        show this help message and exit
  -ip               Network Details for an IP
  -net              All networks within a CIDR (eg. 10.0.0.0/8)
  -nlist            Get all networks in an alert group
  -dev              Get the Details for a Device (Switch/Router/FW)
  -fpath src        Security Path between -fp src dst
  -rpath src        Routed Path between -rp IP/CIDR1 IP/CIDR2
  -spath src        Switched Path between -sp sw1 sw2 (Neo4j Regex)
  -group            Get VLANs for a Management Group
  -vrange 1[-4096]  VLAN Range (default 1-1999)
  -vid              VLAN ID Search
  -vtree            Get the VLAN Tree for a VNAME
  -output TREE      Return Format: TREE, TABLE, CSV, JSON, YAML
  --conf file       Alternate Config File
  --debug DEBUG     Set debugging level
  --verbose         Verbose Output

Examples: netgrph 10.1.1.1 (Free Search for IP), netgrph -net 10.1.1.0/24
(Search for CIDR), netgrph -group MDC (VLAN Database Search), netgrph -fp
10.1.1.1 10.2.2.1 (Firewall Path Search)

```
<br>

### Report Options
```
$ ngreport -h
usage: ngreport [-h] [-vrf name] [-vrfs] [-vlans] [-vrange 1[-4096]] [-dev .*]
                [-output TREE] [-empty] [--conf file] [--debug DEBUG]
                [--verbose]

Generate Reports from NetGrph

optional arguments:
  -h, --help        show this help message and exit
  -vrf name         Generate a Report on a VRF
  -vrfs             VRF Report on all VRFs
  -vlans            VLAN ID Report (combine with -vra and -empty)
  -vrange 1[-4096]  VLAN Range (default 1-1999)
  -dev .*           Report on Network Devices in regex
  -output TREE      Return Format: TREE, TABLE, CSV, JSON, YAML
  -empty            Only Return Empty VLANs (requires NetDB)
  --conf file       Alternate Config File
  --debug DEBUG     Set debugging level
  --verbose         Verbose Output
```

### Discovering a Security Path
```
$ netgrph -fp 10.170.16.1 8.8.8.8

Security Path: 10.170.16.0/24 --> VRF:flex --> PerimeterFW --> VRF:perim -->
               ExternalFW --> VRF:outside --> 0.0.0.0/0

PerimeterFW Logs (15min): [firewall logs link]

ExternalFW Logs (15min): [firewall logs link]
```

### Discovering all equal Switched Paths as CSV between servchas. -> spp2.*
```
$ netgrph -sp servchas. spp2.* -o csv
ChildPort,ChildSwitch,Name,ParentPort,ParentSwitch,_type,distance
Te3/1,servchas1,Link,Eth7/25,core1,SPATH,0
Te1/4,servchas2,Link,Eth8/31,core1,SPATH,0
{...}
```

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

## Motivation

NetGrph was written to explore the potential of graph databases for networks,
and is being shared to help others with network discovery and automation. Please
contribute back any useful additions.


## Planned Features

* Add configuration snippets for each hop on traverals
* Import all Network ACL's for L4 analysis
* Improve NetDB integration with universal search
* Implement Dijkstra's Algorithm for cost-based path traversals (database plugin)
* REST API for nglib queries (Flask Based)
* Simple Web Interface for Path Traversals and report generation
* Statseeker integration for including graphs/errors in reports

## Future

NetGrph will be rapidly evolving at first to meet the needs of network and
security automation in large switched networks. I am open to expanding it for
the needs of MPLS networks and other network/security domains where appropriate.
The application was written to be generic and approachable for use with both SDN
and existing networks.

I have also added some lightweight integration with my existing [NetDB
application](http://netdbtracking.sourceforge.net), but that will be both
focused and optional. If you manage to create any new parsers or integrate with
other vendor APIs, please contribute your code back.

I plan to create a REST API in Flask to return NGTree data-structures for all
queries and reports. I would like to eventually add a GUI as well, but at this
time I'm focussed on using the application to automate tasks. In theory, it
should be easy to create [D3
visualizations](https://github.com/d3/d3/wiki/Gallery) from the NGTree
data-structures. If anyone manages to create a simple GUI or use this
application to create some interesting visualizations, I'd be happy to help and
would love to see the results.

I will not be expanding the application to be a full-blown NMS, but you are free
to fork this code and turn it into anything you like. If you manage to expand
the core modeling functionality and think it should be included in the main
codebase, I'd like to consider including it here.

See the [CONTRIBUTING](CONTRIBUTING.md) document for more information.

## Performance

On our network containing 700+ routers/switches, 2000+ SVIs and 10,000+ VLAN to
switch mappings, performance on almost all netgrph queries is below 150ms. Full
ngreport queries can take longer, but it's for creating network-wide reports.

The database update time on our localhost server with SSDs is 150sec for a
complete network refresh. When importing to an unoptimized VM on a remote
server, the import time is 5min. The network import speed could be dramatically
increased if rewritten using the Bolt driver, which is planned.

## Dependencies

NetGrph is a Python3.4+ application, but could be back-ported to Python2.7
fairly easily. It relies on both the py2neo and neo4j bolt driver (install via
pip3). The plan is to eventually convert all driver code to the bolt driver as
it matures.

NetGrph requires [CSV files](test/csv/) with all of your Switches/Routers, Networks,
VLANs, and CDP/LLDP Neighbors in order to be multi-vendor compatible. I provide
IOS and NXOS configuration parsers, as well as a sample network topology to play
with. For Cisco-based networks, a generic CDP/LLDP mapper is all that's missing.
NetGrph is compatible with NetDB Neighbor Data:
(https://sourceforge.net/projects/netdbtracking/). Once stable, I'll package a
bundled NetDB OVA with NetGrph included.

If anyone has a dependable LLDP/CDP walker they recommend (I'm sure there are
many), please contact me. This only needs src_switch,src_port,dst_switch,dst_port.
I have tested a few different open-source packages, but have yet to find a suitable
tool that is reliable enough.

NetGrph was developed on Ubuntu 14.04 LTS, tested on 16.04, and should be
compatible with other versions of linux. I highly recommend using Ubuntu at this
early stage for better support. I also plan to create an ansible build script in
the next few months.

## Installation

See the [Install Instructions](docs/INSTALL.md)

## Support

I will be monitoring the #netgrph channel the [networktocode slack
group](https://networktocode.herokuapp.com/) for now. Please try and contact me
there for any serious support questions.

## Contributions

Please see the [Contributions](CONTRIBUTING.md) document in docs for
information about how you can contribute back to NetGrph.

## Contributors
* Jonathan Yantis ([yantisj](https://github.com/yantisj))

## License
NetGrph is licensed under the GNU AGPLv3 License.
