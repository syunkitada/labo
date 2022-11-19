FROM ubuntu:20.04

ENV FRRVER="frr-stable"

RUN apt update \
    apt install -y curl lsb-release \
    curl -s https://deb.frrouting.org/frr/keys.asc | apt-key add - \
    echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) $FRRVER | tee -a /etc/apt/sources.list.d/frr.list \
    apt update \
    apt install -y frr frr-pythontools
