# fabfile for Infra As A Code

- fabric によって、yaml ファイルで定義した仕様書からローカルに実験環境を作成できます
- 方針
  - なるべくコードはシェルスクリプトに落とし込んでブラックボックス化を避ける
  - なるべくシェルスクリプト単体でも実行できるようにする

## 使い方

- プロジェクトルートで以下を実行してください

```
# 環境構築（初回だけ実行してください）
$ make env
```

```
# -fで仕様書を指定してinfraを作成します
$ sudo -E .venv/bin/fab make -f infra/local1/spec.yaml

# infraを削除します
$ sudo -E .venv/bin/fab make -f infra/local1/spec.yaml -c clean
```

```
# オプションで特定リソースを指定したり、特定コマンドを指定することができます
# 以下は、node:vm1のコンソールログを出力します
$ sudo -E .venv/bin/fab make -f infra/local1/spec.yaml -t node:vm1 -c log
```

## yaml フォーマット

```
# 汎用設定
common:
  ...

# vmのimage管理用
vm_image_map:
  ...

# テンプレート
template_map:
  ...

# ユニークなリソースを定義する場所(kindが重複できない)
infra_map:
  ...

# リソースを定義する場所(kindは重複してよい)
nodes:
  ...
```
