#!/bin/bash
# this one is a bit of a misnomer
# originally intended to handle on-the-fly key
# generation for https
# now also doing nginx config
echo "Generating Keys..."
echo "Generating crappy Diffie-Hellman Group..."
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 512
# key will be generated to be valid for 10 years...
echo "Key and certificate required for signing key..."
sudo openssl req -x509 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-private-key.key -out /etc/ssl/private/nginx-certificate.crt -sha256 -days 3650 -nodes -subj  "/C=CA/ST=QC/O=TibberTimeframe Inc/CN=TibberTimeframeServer.com"
echo "Done generating keys."

echo "Deleting nginx default config..."
sudo rm /etc/nginx/sites-enabled/default 

echo "Getting and enabling ssl config..."
# default ssl config for our use-case is copied to /var/tmp at container creation
sudo cp /var/tmp/default-ssl /etc/nginx/sites-available
# clean up
sudo rm /var/tmp/default-ssl
# make config available
sudo ln -s /etc/nginx/sites-available/default-ssl /etc/nginx/sites-enabled/default-ssl

# start server
echo "Starting nginx..."
sudo service nginx start
