FROM rockylinux:8

ENV container docker

RUN dnf install -y systemd sudo man vim findutils procps-ng \
                   git wget curl \
                   iptables iputils ethtool traceroute tcpdump wireshark \
                   python3 net-tools iproute

RUN pip3 install --upgrade pip && \
    pip3 install ansible

RUN ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf
RUN systemctl disable rpcbind && \
    systemctl disable crond

CMD ["/usr/sbin/init"]
