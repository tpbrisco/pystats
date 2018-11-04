# Project Title

pystats - certstat

## Introduction

"certstats" allows the probing of remote certificates for HTTPS/TLS.

"certstats" can be ran from the command line, or from a cloud foundry
instance.  Flags -n/--name, -h/--host, -p/--port -c/--cert allow specifics to be
indicated, multiple occurrances of -n/-h/-p/-c can occur for multiple
hosts to be checked.  The '-c/--cert" indicate the directory where
certificates exist.  The "-n/--name" defines a name for that session
-- this allows "certstats" to disambiguate the return values (the JSON
can be specific for a "name" - independent of the host and port).  If
no certificates are indicated, certificates will be used from the
system specific path.

When pushed to a cloud foundry instance, "certstats" provides an API
for probing remote HTTPS/TLS certificates.  The URL '/ccheck' supports
parameters for hostname= and port= and certpath= to verify the TLS
session.

### Dependencies

"certstats" uses Flask and pyOpenSSL.

