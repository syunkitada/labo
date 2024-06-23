FROM rockylinux:9

COPY . /opt/ci-tools

RUN dnf -y install python3-pip

RUN pip install -r /opt/ci-tools/requirements.txt
