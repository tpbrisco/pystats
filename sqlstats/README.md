# Project Title
pystats - sqlstats

## Introduction

"sqlstats" allows the probing of the galera status of a remote database

"sqlstats" can be ran (in a debugging mode) from the command line buy
providing a user, password and remote host (on which is running
mariadb).  The parameters can be provided from environment variables
and/or cli parameters (see get_cmd_opts()).  To ease debugging setup,
"virtualenv" is suggested, with a local installation of the python
dependencies below.

"sqlstats" intended use case is to run in a cloud foundry environment,
and provide a simple means of checking the galera synchronization statistics.

The service can be created from the create-services.sh script - but
the application will bind the the SQL service defined in the manifest.

### Dependencies

"sqlstats" uses Flask, Flask-MySQL and the requests library.
(see requirements.txt)
