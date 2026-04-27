success=1
if [[ "$AUDIOID_SSL_CERTIFICATE_FILE" == "" ]]
then
  echo "AUDIOID_SSL_CERTIFICATE_FILE isn't set."
  success=0
fi

if [[ "$AUDIOID_SSL_CERTIFICATE_KEY_FILE" == "" ]]
then
  echo "AUDIOID_SSL_CERTIFICATE_KEY_FILE isn't set."
  success=0
fi

if [[ "$success" != "1" ]]
then
  echo "qutting due to previous errors."
  exit 1
fi

mod_wsgi-express start-server index.py --log-level debug --log-to-terminal --startup-log --https-port 8123 --https-only --server-name audioid.xyz \
    --ssl-certificate-file "$AUDIOID_SSL_CERTIFICATE_FILE" --ssl-certificate-key-file "$AUDIOID_SSL_CERTIFICATE_KEY_FILE"