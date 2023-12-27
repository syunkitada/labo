FROM rockylinux:8

ENV container docker

RUN dnf install -y systemd sudo man vim findutils procps-ng \
                   git wget curl \
                   iputils ethtool traceroute tcpdump wireshark

RUN ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf
RUN systemctl disable rpcbind && \
    systemctl disable crond

VOLUME [ "/sys/fs/cgroup" ]
CMD ["/usr/sbin/init"]
