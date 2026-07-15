FROM debian:bullseye-slim

LABEL image.author="poseidon.guy@gmail.com"

RUN apt update && \
    apt install -y \
      apache2 \
      apache2-dev \
      apache2-utils \
      python3.9 \
      python3-pip \
      libapache2-mod-wsgi-py3 && \
      apt clean && \
      apt autoremove

RUN mkdir /web
RUN mkdir /web/api
COPY api /web/api
COPY requirements.txt /web

RUN mkdir /var/log/service

WORKDIR /web/api

RUN python3 -m pip install -r /web/requirements.txt

RUN useradd -ms /bin/bash webrunner
RUN chown webrunner .
RUN chown webrunner /var/log/service
USER webrunner

CMD mod_wsgi-express start-server index.py \
      --log-level debug --log-to-terminal --startup-log \
      --port 8080
#      --https-port 8443 --https-only \
#      --server-name # your server name here. \
#      --ssl-certificate-file "$SSL_CERTIFICATE_FILE" --ssl-certificate-key-file "$SSL_CERTIFICATE_KEY_FILE"