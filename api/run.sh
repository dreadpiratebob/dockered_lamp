#success=1
#if [[ "$SSL_CERTIFICATE_FILE" == "" ]]
#then
#  echo "SSL_CERTIFICATE_FILE isn't set."
#  success=0
#fi
#
#if [[ "$SSL_CERTIFICATE_KEY_FILE" == "" ]]
#then
#  echo "SSL_CERTIFICATE_KEY_FILE isn't set."
#  success=0
#fi
#
#if [[ "$success" != "1" ]]
#then
#  echo "qutting due to previous errors."
#  exit 1
#fi

mod_wsgi-express start-server index.py \
    --log-level debug --log-to-terminal --startup-log \
    --port 8080
#    --https-port 8443 --https-only \
#    --server-name # your server name here. \
#    --ssl-certificate-file "$SSL_CERTIFICATE_FILE" --ssl-certificate-key-file "$SSL_CERTIFICATE_KEY_FILE"