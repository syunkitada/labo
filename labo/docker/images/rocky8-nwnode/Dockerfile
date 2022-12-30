FROM rockylinux:8

ENV container docker
ENV FRRVER="frr-stable"

# setup for systemd
# RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
#     systemd-tmpfiles-setup.service ] || rm -f $i; done); \
#     rm -f /lib/systemd/system/multi-user.target.wants/*;\
#     rm -f /etc/systemd/system/*.wants/*;\
#     rm -f /lib/systemd/system/local-fs.target.wants/*; \
#     rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
#     rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
#     rm -f /lib/systemd/system/basic.target.wants/*;\
#     rm -f /lib/systemd/system/anaconda.target.wants/*;

RUN yum install -y systemd

# frr
RUN yum install -y https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el8.noarch.rpm && \
    yum install -y frr frr-pythontools

# ovs
# http://ftp.nara.wide.ad.jp/pub/Linux/centos/8-stream/cloud/x86_64/openstack-yoga/Packages/
RUN yum install -y https://repos.fedorapeople.org/repos/openstack/openstack-yoga/rdo-release-yoga-1.el8.noarch.rpm && \
    yum install -y rdo-openvswitch python3-rdo-openvswitch

# tools
RUN yum install -y tcpdump traceroute vim ethtool sudo iputils httpd wireshark
RUN yum install -y man

VOLUME [ "/sys/fs/cgroup" ]
CMD ["/usr/sbin/init"]
