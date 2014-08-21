# Docker Magical Initialisation

[![Build Status](https://travis-ci.org/voltgrid/voltgrid-pie.svg?branch=master)](https://travis-ci.org/voltgrid/voltgrid-pie)

_voltgrid.py_ provides a configuration based approach for code deployment.


When used with [Docker](https://www.docker.com/) _voltgrid.py_ can handle 100% of your container bootstraping and code deployment.

Here is a Docker `CMD` example that uses [bureaucrat](https://github.com/adlibre/python-bureaucrat) for process management and environment contextualisation:


    CMD ["/usr/local/bin/voltgrid.py", "/srv/ve27/bin/bureaucrat", "init", "--venv", "/srv/ve27", "--envfile", "/srv/env", "--app", "/srv/git", "--logpath", "/srv/log", "--pidpath", "/var/tmp"]
