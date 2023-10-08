FROM ubuntu:22.04

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
    sudo gnupg2 vim git gcc \
    python3-venv python3-dev \
    curl wget tcpdump traceroute wireshark tshark \
    iputils-ping iputils-tracepath iputils-arping iproute2

RUN ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf && \
    systemctl disable cron && \
    systemctl disable systemd-resolved && \
    systemctl disable systemd-timesyncd

ENTRYPOINT ["/usr/sbin/init"]
