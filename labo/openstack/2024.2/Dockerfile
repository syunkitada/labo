FROM rockylinux:9

ENV container docker

RUN dnf install -y systemd sudo man vim findutils procps-ng \
                   git wget ca-certificates openssh-server \
                   iptables iputils ethtool traceroute tcpdump wireshark \
                   net-tools iproute

CMD ["/usr/sbin/init"]
