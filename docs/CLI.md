# CLI Documentation

NetGrph has two CLI query programs, netgrph.py and ngreport.py. The first is for
queries such as networks, paths etc. The second is for network-wide reporting on
devices, VRFs etc.

## Query Options
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

## Report Options
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
