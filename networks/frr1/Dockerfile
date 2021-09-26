FROM centos:centos7

ENV FRRVER="frr-stable"

RUN curl -O https://rpm.frrouting.org/repo/$FRRVER-repo-1-0.el7.noarch.rpm && \
    yum install -y ./$FRRVER* && \
    yum install -y frr frr-pythontools \
    yum install -y vim
