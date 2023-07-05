#!/bin/bash

# Define where you want to generate the certificate and key pair
DIR="llm/server/cert"

# Check if command line argument is given (exit with an error otherwise)
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <ip_address>"
    exit 1
fi

# Check if the given argument is a valid IP (exit with an error otherwise)
if ! echo "$1" | grep -P '^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$' > /dev/null; then
    echo "Error: invalid IP address"
    exit 1
fi

# Create directory if it doesn't exist
mkdir -p $DIR

# The IP address is the first command line argument
SERVER_IP=$1

# Create SAN configuration file for your IP
cat <<EOF > $DIR/san.cnf
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req

[req_distinguished_name]
commonName = Common Name (e.g. server FQDN or YOUR name)
commonName_default = $SERVER_IP

[v3_req]
subjectAltName = @alt_names

[alt_names]
IP.1 = $SERVER_IP
EOF

# Generate your CA key and certificate
openssl req -x509 -newkey rsa:4096 -days 365 -nodes -keyout $DIR/my-ca.key -out $DIR/my-ca.crt -subj "/CN=my-ca"

# Create a server key and certificate signing request (CSR) 
openssl req -new -newkey rsa:4096 -days 365 -nodes -keyout $DIR/server.key -out $DIR/server.csr -subj "/CN=$SERVER_IP" -config $DIR/san.cnf

# Sign the server CSR with the self-signed CA key and certificate, creating the server certificate:
openssl x509 -req -in $DIR/server.csr -CA $DIR/my-ca.crt -CAkey $DIR/my-ca.key -CAcreateserial -out $DIR/server.crt -extensions v3_req -extfile $DIR/san.cnf -days 365