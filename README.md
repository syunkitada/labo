# My Labo

- 実験用のスクリプトやメモ書きを置く場所です

## Directory Structure

| Link                   | Description                                |
| ---------------------- | ------------------------------------------ |
| [src](src)             | mylabo のソースコードです                  |
| [tests](tests)         | テストコードです                           |
| [manifests](manifests) | 実験用の manifest ファイルの置き場です     |
| [labo](labo)           | 実験用のスクリプトやメモ書きを置く場所です |

## Setup

### 1. Install uv

https://docs.astral.sh/uv/getting-started/installation/

### 2. Initaial setup

```
$ git clone https://github.com/syunkitada/labo.git
$ cd labo
$ uv sync --extra dev
$ uv pip install -e .
```

```
$ sudo mkdir -p /etc/ansible/host_vars
$ cp etc/ansible/host_vars/localhost.yml /etc/ansible/host_vars/localhost.yaml
$ vim /etc/ansible/host_vars/localhost.yaml
< local_ipaddr: "{{ CHANGE_ME }}"
---
> local_ipaddr: "192.168.XX.YY"
```

```
$ cd labo/tls; make; cd -
$ sudo uv run ansible-playbook labo.infra.labo
$ sudo uv run mylabo apply -f manifests/dns
```

## How to use mylabo

```
$ sudo uv run mylabo -l
Available tasks:

  apply    apply -f [file] -d -D -l [labels]
  debug    debug -f [file] -d -D -l [labels]
  delete   delete -f [file] -d -D -l [labels]
  get      get -f [file] -d -D -l [labels]
  test     test -f [file] -d -D -l [labels]
```

```
# Example
$ sudo uv run mylabo apply -f manifests/infras/ovs/vxlan/vxlan5.1.yml
```

## Developping

### Helpers

```
# Testing
$ make test

# Linting
$ make lint

# Formatting
$ make format
```
