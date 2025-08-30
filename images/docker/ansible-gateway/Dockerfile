FROM rockylinux:9

RUN dnf install -y \
    systemd sudo wget procps-ng findutils \
    man vim git \
    ca-certificates openssh-server openssh-clients \
    iptables iputils ethtool traceroute tcpdump wireshark net-tools iproute \
    python3 python3-pip

# Install ansible
RUN pip install --upgrade pip && \
    pip install ansible

# RUN update-ca-trust \
#     && ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf

CMD ["/usr/sbin/init"]
