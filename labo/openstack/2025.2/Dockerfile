FROM rockylinux:9

RUN dnf install -y epel-release && \
    dnf install -y \
       systemd sudo man vim findutils procps-ng \
       git wget ca-certificates openssh-server \
       iptables iputils ethtool traceroute tcpdump wireshark \
       net-tools iproute \
       python3.12 python3.12-devel python3.12-pip \
       uwsgi uwsgi-plugin-python312

CMD ["/usr/sbin/init"]
