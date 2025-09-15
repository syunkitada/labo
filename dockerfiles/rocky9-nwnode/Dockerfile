FROM local/rocky9-base

# frr
RUN dnf install -y https://rpm.frrouting.org/repo/frr-stable-repo-1-0.el9.noarch.rpm && \
    dnf install -y frr frr-pythontools

# ovs
# https://docs.openstack.org/ja/install-guide/environment-packages-rdo.html
RUN dnf install -y centos-release-openstack-dalmatian && \
    dnf install -y rdo-openvswitch python3-rdo-openvswitch
