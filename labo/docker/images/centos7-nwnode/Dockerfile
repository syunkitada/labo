FROM centos:7

ENV container docker
ENV FRRVER="frr-stable"

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
RUN yum install -y tcpdump traceroute vim ethtool sudo iputils httpd

VOLUME [ "/sys/fs/cgroup" ]
CMD ["/usr/sbin/init"]
