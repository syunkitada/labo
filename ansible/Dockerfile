FROM local/rocky9-base

COPY . /etc/ansible

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

CMD ["/usr/sbin/init"]
