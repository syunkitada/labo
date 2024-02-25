FROM centos:7

ENV container docker
ENV FRRVER="frr-stable"

RUN yum install -y systemd


# 参考: [Systemdを使えるCentOSをDockerコンテナで立ててみた](https://qiita.com/kaburankattara/items/22e63d3861fc2f4f021e)
# 注意: 親のcgroupをマウントする必要があるが、cgroupのバージョンがv1である必要がある
# v2を利用する場合は、systemdのバージョンが247以上である必要がある

# setup for systemd
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
    systemd-tmpfiles-setup.service ] || rm -f $i; done); \
    rm -f /lib/systemd/system/multi-user.target.wants/*;\
    rm -f /etc/systemd/system/*.wants/*;\
    rm -f /lib/systemd/system/local-fs.target.wants/*; \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*;\
    rm -f /lib/systemd/system/anaconda.target.wants/*;

# frr
RUN yum install -y https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el7.noarch.rpm && \
    yum install -y frr frr-pythontools

# ovs
RUN yum install -y https://repos.fedorapeople.org/repos/openstack/openstack-train/rdo-release-train-1.noarch.rpm && \
    yum install -y openvswitch python-openvswitch

# tools
RUN yum install -y tcpdump traceroute vim ethtool sudo iputils httpd iptables

VOLUME [ "/sys/fs/cgroup" ]
CMD ["/usr/sbin/init"]
