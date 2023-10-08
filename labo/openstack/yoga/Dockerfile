FROM labo/ubuntu22-base
MAINTAINER Shunya Kitada syun.kitada@gmail.com

ENV WD=/opt/openstack
ENV TZ=Asia/Tokyo

COPY . /tmp/

RUN mkdir -p $WD

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# install common requirements
RUN apt update && \
    apt install -y \
    mysql-server \
    memcached \
    rabbitmq-server

# install openstack clients
RUN cd $WD && \
    python3 -m venv /opt/osclient --system-site-packages && \
    /opt/osclient/bin/pip install -r /tmp/osclient/requirements.txt

# install keystone requirements
RUN cd $WD && \
    python3 -m venv /opt/keystone --system-site-packages && \
    /opt/keystone/bin/pip install -r /tmp/keystone/requirements.txt && \
    git clone https://github.com/openstack/keystone.git -b stable/yoga && \
    cd keystone && /opt/keystone/bin/python setup.py install

# install glance requirements
RUN cd $WD && \
    python3 -m venv /opt/glance --system-site-packages && \
    /opt/glance/bin/pip install -r /tmp/glance/requirements.txt && \
    git clone https://github.com/openstack/glance.git -b stable/yoga && \
    cd glance && /opt/glance/bin/python setup.py install

# install placement requirements
RUN cd $WD && \
    python3 -m venv /opt/placement --system-site-packages && \
    /opt/placement/bin/pip install -r /tmp/placement/requirements.txt && \
    git clone https://github.com/openstack/placement.git -b stable/yoga && \
    cd placement && /opt/placement/bin/python setup.py install

# install neutron requirements
RUN cd $WD && \
    python3 -m venv /opt/neutron --system-site-packages && \
    /opt/neutron/bin/pip install -r /tmp/neutron/requirements.txt && \
    git clone https://github.com/openstack/neutron.git -b stable/yoga && \
    cd neutron && /opt/neutron/bin/python setup.py install && \
    git clone https://github.com/openstack/neutron-lib.git -b stable/yoga && \
    cd neutron-lib && /opt/neutron/bin/python setup.py install

# install nova requirements
RUN cd $WD && \
    python3 -m venv /opt/nova --system-site-packages && \
    /opt/nova/bin/pip install -r /tmp/nova/requirements.txt && \
    git clone https://github.com/openstack/nova.git -b stable/yoga && \
    cd nova && /opt/nova/bin/python setup.py install

# install virt pkgs for nova
RUN apt install -y \
    novnc \
    qemu-kvm libvirt-daemon-system
