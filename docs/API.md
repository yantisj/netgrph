# API Documentation

* The API is currently under development and in flux.
* Version 1.1 documentation
* Base URL: /netgrph/api/v1.1

### Setup
* Configure the [api] section in netgrph.ini
* Enable HTTPS with valid certs for listening beyond localhost
* Initialize the SQL Lite database: ```./ctlsrv.py --initdb```
* Add an API User: ```./ctlsrv --adduser testuser```
* Run the Server: ```./ctlsrv.py --run```
* Test a Query: ```curl -u testuser:testpass http://localhost:4096/netgrph/api/v1.1/devs```


### Device Queries

Device Queries allow you to query the API for all devices, regexes and gather
specific information from individual devices.

#### Device Get Options

* group: regex on device groups
* search: regex on device names
* full: Return full device reports instead of truncating reports (slower)

#### Query Options

* /devs - list of all devices
* /devs/{device} - specific device
* /devs/{device}/vlans - device vlans
* /devs/{device}/neighbors - device neighbors
* /devs/{device}/nets - device networks
* /devs?search='.*' - search on devices via regex
* /devs?group='.*' - search on management group via regex
* /devs?full=1 - get full device reports

### Networks

* /nets - list of all networks
* /nets?group=X
* /nets?cidr=X
* /nets?ip=X
* /nets?list=X
* /nets?filter=X


* /vlans
* /vlans&vid=X
* /vlans&vname=X
* /vlans&group=X


* /path
* /spath
* /rpath
* /fpath
