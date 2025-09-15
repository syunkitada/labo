# Labo

- 実験用のスクリプトやメモ書きを置く場所です

## ディレクトリ構成

| リンク                         | 説明                                                 |
| ------------------------------ | ---------------------------------------------------- |
| [fabfile](fabfile)             | fabric によって実験環境を構築するための fabfile です |
| [fabfile_tests](fabfile_tests) | fabfile のテストコードです                           |
| [infra](infra)                 | 実験環境の spec ファイルの置き場です                 |
| [labo](labo)                   | 実験用のスクリプトやメモ書きを置く場所です           |

## 初回セットアップ

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
$ cd labo/tls; make
$ sudo .venv/bin/ansible-playbook labo.infra.labo
$ sudo .venv/bin/mylabo apply -f manifests/dns_record.yml
```

### 3. Activate virtual env

```
$ source .venv/bin/activate
```

### 4. Apply manifests

```
$ sudo .venv/bin/mylabo apply -f manifests/infras/vm/rocky9.yml

$ sudo .venv/bin/mylabo apply -f manifests/infras/ovs/vxlan/vxlan5.1.yml
$ sudo .venv/bin/mylabo test -f manifests/infras/ovs/vxlan/vxlan5.1.yml
```

## Developping

### Testing

```
$ uv run pytest

# Test the specific code and get cov report
$ uv run pytest tests/unittest/lib/manifest/test_manifest_template.py --cov=mylabo.lib.manifest.manifest_template --cov-report=term-missing
```
