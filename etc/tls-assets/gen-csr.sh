sudo apt -y install golang-cfssl

test /mnt/nfs/tls-assets && exit 0 || echo "ignored"

rm -rf tmp
mkdir -p tmp
cd tmp || exit 1

cfssl gencert -config ../ca-config.json -initca ../ca-csr.json | cfssljson -bare ca
cfssl gencert \
	-ca=ca.pem \
	-ca-key=ca-key.pem \
	-config=../ca-config.json \
	-hostname=192.168.10.121,127.0.0.1 \
	-profile=server \
	../server-csr.json | cfssljson -bare server

cd - || exit 1

sudo rm -rf /mnt/nfs/tls-assets
sudo cp -r tmp /mnt/nfs/tls-assets

# rocky8
# cp /mnt/nfs/tls-assets/ca.pem /usr/share/pki/ca-trust-source/anchors/
# sudo update-ca-certificates

# ubuntu22
# sudo cp /mnt/nfs/tls-assets/ca.pem /usr/local/share/ca-certificates/self-ca.crt
# sudo update-ca-certificates
