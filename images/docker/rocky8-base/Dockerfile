FROM rockylinux:8

ENV container docker

COPY etc/tls-assets/tmp/ca.pem /usr/share/pki/ca-trust-source/anchors/self-ca.crt

RUN dnf install -y systemd sudo man vim findutils procps-ng \
                   git wget curl ca-certificates \
                   iptables iputils ethtool traceroute tcpdump wireshark \
                   python3 net-tools iproute

RUN pip3 install --upgrade pip && \
    pip3 install ansible

RUN update-ca-trust \
    && ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf \
    && systemctl disable rpcbind \
    && systemctl disable crond

CMD ["/usr/sbin/init"]
