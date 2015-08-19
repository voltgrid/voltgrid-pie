# Ubuntu Apache PHP Example

This is an example of using `voltgrid.py` with a PHP application running on Ubuntu.

## Build Example

```
git clone https://github.com/voltgrid/voltgrid-pie
cd voltgrid-pie/docs/examples/ubuntu
docker built -t voltgrid-pie-example .
```

## Run example

```
# Simple start
$ docker run --rm -ti -p 8080:8080 voltgrid-pie-example

# Checkout a git repo
$ docker run --rm -ti -e "GIT_URL=http://10.0.200.200/roundcube.git" -p 8080:8080 voltgrid-pie-example

# Change some config
$ docker run --rm -ti -e "SERVERNAME=www.example.com" -p 8080:8080 voltgrid-pie-example /usr/local/bin/voltgrid.py cat /etc/apache2/sites-enabled/000-default.conf

# More complex config change
$ docker run --rm -ti -e 'SERVERNAMES=["example.com","www.example.com","example.net","www.example.net"]' -p 8080:8080 voltgrid-pie-example /usr/local/bin/voltgrid.py cat /etc/apache2/sites-enabled/000-default.conf

# Putting it all together and changing the port
$ docker run --rm -ti -e 'SERVERNAMES=["example.com","www.example.com","example.net","www.example.net"]' -e 'PORT=8081' -e 'GIT_URL=http://10.0.200.200/wordpress.git' -p 8081:8081 voltgrid-pie-example
```
