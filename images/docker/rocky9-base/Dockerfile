FROM rockylinux:9

ENV container docker

COPY etc/tls-assets/tmp/ca.pem /usr/share/pki/ca-trust-source/anchors/self-ca.crt

RUN dnf install -y systemd sudo man vim findutils procps-ng \
                   git wget ca-certificates openssh-server \
                   iptables iputils ethtool traceroute tcpdump wireshark \
                   net-tools iproute

RUN update-ca-trust \
    && ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf \
    && systemctl enable sshd

CMD ["/usr/sbin/init"]
