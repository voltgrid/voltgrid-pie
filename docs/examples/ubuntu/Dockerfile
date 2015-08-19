FROM ubuntu:14.04

RUN \
  apt-get -y -q update && \
  apt-get -y -q install python3-jinja2 git && \
  apt-get -y -q install apache2 libapache2-mod-php5 php5-cli php5-mysql php-pear && \
  pear install channel://pear.php.net/Net_IDNA2-0.1.1 && \
  apt-get -y -q clean

ADD https://raw.githubusercontent.com/voltgrid/voltgrid-pie/master/voltgrid.py /usr/local/bin/voltgrid.py
COPY voltgrid.conf /usr/local/etc/voltgrid.conf

ENV APACHE_PID_FILE /var/run/apache2/apache2.pid
ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
ENV APACHE_LOCK_DIR /var/lock/apache2

COPY ports.conf /etc/apache2/ports.conf
COPY apache2.conf /etc/apache2/apache2.conf
COPY 000-default.conf /etc/apache2/sites-available/000-default.conf

RUN \
  rm -f /var/www/html/index.html && \
  chown -R www-data:www-data /var/log/apache2 /var/run/apache2 && \
  ln -s /usr/bin/python3.4 /usr/bin/python && \
  chmod +x /usr/local/bin/voltgrid.py

CMD ["/usr/local/bin/voltgrid.py","/usr/sbin/apache2","-e","info","-D","FOREGROUND"]
