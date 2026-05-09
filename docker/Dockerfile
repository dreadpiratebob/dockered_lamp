FROM ubuntu:22.04

RUN apt-get upgrade -y && \
    apt-get install software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get install -y \
      apache2 \
      apache2-dev \
      apache2-utils \
      python3.9

RUN python -m ensurepip --upgrade && \
    python -m pip install \
      mod-wsgi \
      pymysql \
      urllib

RUN mkdir /web
COPY api /web
WORKDIR /web/api

CMD mod_wsgi-express start-server index.py \
      --log-level debug --log-to-terminal --startup-log \
      --port 8080
#      --https-port 8443 --https-only \
#      --server-name # your server name here. \
#      --ssl-certificate-file "$SSL_CERTIFICATE_FILE" --ssl-certificate-key-file "$SSL_CERTIFICATE_KEY_FILE"