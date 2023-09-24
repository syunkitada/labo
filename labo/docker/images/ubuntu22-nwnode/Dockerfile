FROM ubuntu:22.04


ENV FRRVER="frr-stable"

RUN apt update && \
    apt install -y sudo curl wget gnupg2 gcc

RUN curl -s https://deb.frrouting.org/frr/keys.asc | apt-key add - && \
    RELEASE=`cat /etc/os-release | grep VERSION_CODENAME | awk -F '=' '{print $2}'` && \
    echo deb https://deb.frrouting.org/frr $RELEASE $FRRVER | tee /etc/apt/sources.list.d/frr.list && \
    apt update && apt install -y frr frr-pythontools

RUN apt install -y vim tcpdump traceroute wireshark tshark \
                   iputils-ping iputils-tracepath iputils-arping iproute2

RUN ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf && \
    systemctl disable cron && \
    systemctl disable systemd-resolved && \
    systemctl disable systemd-timesyncd

ENTRYPOINT ["/usr/sbin/init"]
