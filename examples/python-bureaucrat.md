### Example _Dockerfile_

    # Volt Grid: Volt Grid Pie / Bureaucrat Example
    #
    # Base: centos7
    # Version: 1.0.0

    FROM centos:centos7

    RUN rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 && \
        yum -q -y update && \
        yum -q -y install curl git tar bzip2 python-jinja2 && \
        yum -q -y install gcc freetype ghostscript freetype-devel libpng libjpeg-turbo libpng-devel libjpeg-turbo-devel python-devel libxml2-devel libxslt-devel mariadb-devel && \
        yum -q -y install make openssl-devel sqlite-devel libffi-devel bzip2-devel && \
        yum -q clean all

    # Consistent uid for web user
    RUN groupadd www --gid 48 && useradd www --uid 48 --gid 48 -d /srv/www && mkdir /srv/log && \
        chown -R www:www /srv

    # Git SSH Setup
    RUN mkdir /root/.ssh && chmod 700 /root/.ssh && echo -e "Host *\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config && \
        mkdir /srv/git && chown root:root /srv/git

    # Create Python 2.7 Virtual Env
    USER www
    RUN cd /srv && \
        curl --silent https://raw.githubusercontent.com/adlibre/python-bootstrap/master/bootstrap.sh | bash -s ve27 bureaucrat

    # Add Volt Grid .py / .conf
    USER root
    ADD voltgrid.conf.example /usr/local/etc/voltgrid.conf
    ADD voltgrid.py /usr/local/bin/voltgrid.py
    RUN chmod 755 /usr/local/bin/voltgrid.py && chmod 644 /usr/local/etc/voltgrid.conf

    EXPOSE 8000
    USER root
    CMD ["/usr/local/bin/voltgrid.py", "/srv/ve27/bin/bureaucrat", "init", "--venv", "/srv/ve27", "--envfile", "/srv/.env", "--app", "/srv/git", "--logpath", "/srv/log", "--pidpath", "/var/tmp"]

#### Build the container

    docker build -t voltgrid/example .

#### Deploy the container


To deploy the [Django Sample app](https://github.com/adlibre/voltgrid-django-sample):

    docker run -P -e "GIT_URL=https://github.com/adlibre/voltgrid-django-sample.git" \
      -e "DEBUG=True" \
      -e "PORT=8000" \
      -e "SECRET_KEY=secret" \
      -e "WORKERS=4" \
      -e "LOGFILE=/srv/log/web.log" \
      -v /docker/log:/srv/log \
      -v /docker/remote/:/srv/remote/ \
      -t voltgrid/example

NB. _voltgrid.py_ assumes that certain mounts are available.
