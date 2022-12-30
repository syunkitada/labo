# fabfile for Infra As A Code

- fabric によって、yaml ファイルで定義した仕様書からローカルに実験環境を作成できます
- 方針
  - なるべくコードはシェルスクリプトに落とし込んでブラックボックス化を避ける
    - シェルスクリプトは後から確認したり単体でも実行できるようにする
- [仕様書](spec.md)

## 使い方

- プロジェクトルートで以下を実行してください

```
# ローカルの初回環境構築（初回だけ実行してください）
$ make env
```

```
# -fで仕様書(spec.yaml)を指定して実験環境を作成します
$ sudo -E .venv/bin/fab make -f infra/local1/spec.yaml

# 実験環境を削除します
$ sudo -E .venv/bin/fab make -f infra/local1/spec.yaml -c clean
```

```
# オプションで特定リソースを指定したり、特定コマンドを指定することができます
# 以下は、node:vm1のコンソールログを出力します
$ sudo -E .venv/bin/fab make -f infra/local1/spec.yaml -t node:vm1 -c log
```
