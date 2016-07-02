## Contributions

These are the early days of NetGrph, but I fully plan to support this program
going forward and am looking for contributors. I am also the primary maintainer
of the [Network Tracking Database
(NetDB)](http://netdbtracking.sourceforge.net/), which is in production on some
extremely large network. NetGrph is currently serving as our internal model for
network automation tasks, and we hope others find it useful as well. It's
primary purpose is to do work at this time, from automation to troubleshooting
tasks.

### Data Sources

NetGrph is short on data sources at this time, so if you manage to generate the
necessary [CSV files](csv/) for your network, I will most likely accept them in
to the repository without much trouble. All source data is CSV based to make it
easy for others to contribute to the project. Please explore those files for
understanding how to get your network data in to the program.

I am considering using [Napalm](https://github.com/napalm-automation/napalm) in
the future for a more robust data gathering source, but at the moment I will be
busy integrating this application in to our automation and troubleshooting test
suite. If you have some ideas or would like to work on this, please contact me
on Slack. I am open to any and all solutions at the moment, as long as they are
simple, maintainable and based off of other open-source network tools.

### Core Library Changes

[nglib](nglib/) is the core library of the application. Currently, the only code
using the library are the CLI scripts netgrph, ngupdate and ngreport. This
application was written with APIs in mind though, so the next phase after
finishing up all the reporting and user functionality via the CLI will be to
create an API via Flask. I will also be creating some user facing
troubleshooting GUI tools, but at this time, the GUI plans are quite simple.
That said, there is no reason via nglib and a framework like Flask, that this
could not be developed in to a full fledged GUI app.

If you submit a pull request on the core library, please make sure you put your
code through the pylint process and follow the existing code style. If you have
any concerns about whether your code will be accepted, please contact me on
Slack. I'd like to see contributions beyond simple data sources as long as they
don't break the data model or complicate the maintainability of the code. This
is very much an experimental program at this time, so I'm open to new directions
from here.
