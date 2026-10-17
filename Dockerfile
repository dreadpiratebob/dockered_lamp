FROM debian:bookworm-slim

LABEL image.author="heinrichhoza1.02@gmail.com"

RUN groupadd webrunner \
 && useradd -ms /bin/bash -g webrunner webrunner

ENV APACHE_LOG_DIR=/var/log/apache2 \
    APACHE_PID_FILE=/var/run/apache2/apache2.pid \
    APACHE_RUN_DIR=/var/run/apache2 \
    APACHE_RUN_USER=webrunner \
    APACHE_RUN_GROUP=webrunner \
    APACHE_SERVER_NAME=webrunner

RUN apt update \
 && apt install -y \
      apache2 \
      apache2-dev \
      apache2-utils \
      python3.11 \
      python3.11-venv \
      python3-pip \
      libapache2-mod-wsgi-py3 && \
      apt clean && \
      apt autoremove

RUN echo "" >> /etc/apache2/apache2.conf \
 && echo "ServerName $APACHE_SERVER_NAME" >> /etc/apache2/apache2.conf \
 && service apache2 restart

RUN mkdir /web \
 && mkdir /web/api
COPY api /web/api
COPY requirements.txt /web

RUN mkdir /var/log/service

WORKDIR /web/api
RUN chown webrunner . \
 && chown webrunner /var/log/service

USER webrunner

RUN python3 -m venv . \
 && chmod +x ./bin/activate
RUN . ./bin/activate
RUN ./bin/pip3.11 install wheel \
 && ./bin/pip3.11 install -r /web/requirements.txt

CMD . ./bin/activate \
 && mod_wsgi-express start-server index.py \
      --log-level debug --log-to-terminal --startup-log \
      --port 8080
#      --https-port 8443 --https-only \
#      --server-name # your server name here. \
#      --ssl-certificate-file "$SSL_CERTIFICATE_FILE" --ssl-certificate-key-file "$SSL_CERTIFICATE_KEY_FILE"