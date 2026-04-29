FROM debian:stable-slim

RUN apt-get update && \
    apt-get install -y \
      python3.9
RUN python -m ensurepip --upgrade
RUN python -m pip install mod-wsgi

RUN mkdir /web
COPY api /web
WORKDIR /web/api

CMD mod_wsgi-express start-server index.py \
      --log-level debug --log-to-terminal --startup-log \
      --port 8080
#      --https-port 8443 --https-only \
#      --server-name # your server name here. \
#      --ssl-certificate-file "$SSL_CERTIFICATE_FILE" --ssl-certificate-key-file "$SSL_CERTIFICATE_KEY_FILE"