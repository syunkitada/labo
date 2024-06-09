FROM rockylinux:9

COPY etc/tls-assets/tmp/ca.pem /usr/share/pki/ca-trust-source/anchors/self-ca.crt

RUN dnf install -y ca-certificates systemd sudo man vim findutils procps-ng \
                    python3 python3-pip openssh-clients git

# Install ansible
RUN pip install --upgrade pip && \
    pip install ansible

# Install helm
RUN curl -Lo helm.tar.gz https://get.helm.sh/helm-v3.14.3-linux-amd64.tar.gz && \
    tar xf helm.tar.gz && \
    install -o root -g root -m 0755 linux-amd64/helm /usr/bin/helm && \
    rm -rf linux-amd64 && \
    rm helm.tar.gz && \
    helm plugin install https://github.com/databus23/helm-diff

# Install kind
RUN curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64 && \
    install -o root -g root -m 0755 kind /usr/bin/kind && \
    rm ./kind

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/bin/kubectl && \
    rm ./kubectl

RUN update-ca-trust \
    && ls /lib/systemd/system/*.wants/* | grep -v journald | xargs rm -rf

CMD ["/usr/sbin/init"]
