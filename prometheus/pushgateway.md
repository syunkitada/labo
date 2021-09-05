# pushgateway

- [github](https://github.com/prometheus/pushgateway)

## 概要

- ラベリングについて
  - Prometheus は、scrape したメトリクスに job ラベルと instance ラベルを添付する
  - Prometheus の scrape config に、honor_labels: true とすると、pushgateway 側のラベルが優先される
- push されたメトリクスは、pushgateway の/metrics エンドポイントで、pushgateway 自体のメトリクスと一緒に公開される
- 起動オプションに、--persistence.file を指定するとデータが永続化される
  - 基本的に一時的なメトリクス置き場なので永続化する必要性は低い

## Push

- メトリクスは、/metrics/job/[jobName]/instance/[instanceName] に対して POST すると登録できる
- /metrics/job/[jobName] に対して POST しても登録できるが、このときは instance=""のラベルが登録される
  - instance=""で登録するのは、prometheus による上書きを防止するため
- 厳密には以下なパス指定によってラベルを付与できる
  - /metrics/job/<JOB_NAME>{/<LABEL_NAME>/<LABEL_VALUE>}

```
cat <<EOF | curl --data-binary @- http://127.0.0.1:9091/metrics/job/some_job/instance/some_instance
# TYPE some_metric counter
some_metric{label="val1"} 42
# TYPE another_metric gauge
# HELP another_metric Just an example.
another_metric 2398.283
EOF
```

- Push の正常性判断
  - バッチシステムが定期的にメトリクスを送ってるかを判断するためには、そのメトリクスを見るだけでは判断できない
    - 一度でも Push されれば、そのメトリクスが更新されようがされまいが、Prometheus からはそのメトリクスが最新のものとみなすため
    - Prometheus の仕様からメトリクス自体には timestamp は付与されず、Prometheus からそれが新しいのかどうかを確かめる手段がない
  - push_time_seconds
    - このメトリクスは push 成功時の UNIX タイムが登録され、push されるたびに更新される
    - これによってメトリクスが更新され続けているかを判断できる
  - push_failure_time_seconds
    - このメトリクスは push 失敗時の UNIX タイムが登録され、push が失敗するたびに更新される
    - これによって push が成功したかどうかを判断できる

```
# TYPE check_pusher1 untyped
check_pusher1{instance="pusher1",job="push_job",label1="val1"} 0
# TYPE check_pusher2 untyped
check_pusher2{instance="pusher1",job="push_job",label1="val1"} 1
push_failure_time_seconds{instance="pusher1",job="push_job"} 0
push_time_seconds{instance="pusher1",job="push_job"} 1.630841009101454e+09
```

## Delete

- push 時のパスをそのまま使い、HTTP メソッドを DELETE にすればメトリクスを削除できる

```
curl -X DELETE http://pushgateway.example.org:9091/metrics/job/some_job/instance/some_instance
```
