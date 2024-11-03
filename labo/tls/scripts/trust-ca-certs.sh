# Trust self CA cert
if grep "Ubuntu 22" /etc/os-release; then
	sudo cp "${CA_PEM_PATH}" /usr/local/share/ca-certificates/self-ca.crt
	sudo update-ca-certificates
fi

if grep "Rocky" /etc/os-release; then
	sudo cp "${CA_PEM_PATH}" /usr/share/pki/ca-trust-source/anchors/
	sudo update-ca-trust
fi
