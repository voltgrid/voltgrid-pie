# Magical Deployments

[![Build Status](https://travis-ci.org/voltgrid/voltgrid-pie.svg?branch=master)](https://travis-ci.org/voltgrid/voltgrid-pie)

_voltgrid.py_ provides a configuration based approach to code deployment and configuration.

## Features

 * Environment Variable Contextualisation
 * Git checkout
 * Configuration file templating

## Docker Support

When used with [Docker](https://www.docker.com/) _voltgrid.py_ can handle 100% of your container bootstraping and code deployment.

## Examples

[Ubuntu PHP](docs/examples/ubuntu/README.md)

[Python Bureaucrat](docs/examples/python-bureaucrat.md)

## Development and testing

Clone this repo into the root of a virtualenv.

1. Install the requirements

    `pip install -r requirements.txt`

2. Hack away.

3. Test

    `py.test -v tests`

4. Commit your changes
