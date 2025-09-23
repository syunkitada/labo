FROM local/rocky8-base

ENV container docker
ENV FRRVER="frr-stable"

# frr
RUN yum install -y https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el8.noarch.rpm && \
    yum install -y frr frr-pythontools

# ovs
# http://ftp.nara.wide.ad.jp/pub/Linux/centos/8-stream/cloud/x86_64/openstack-yoga/Packages/
RUN yum install -y https://repos.fedorapeople.org/repos/openstack/openstack-yoga/rdo-release-yoga-1.el8.noarch.rpm && \
    yum install -y rdo-openvswitch python3-rdo-openvswitch

# tools
RUN yum install -y httpd
