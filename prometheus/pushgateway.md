# pushgateway

## push

- /metrics/job/[jobName]/instance/[instanceName]

```
cat <<EOF | curl --data-binary @- http://127.0.0.1:9091/metrics/job/some_job/instance/some_instance
# TYPE some_metric counter
some_metric{label="val1"} 42
# TYPE another_metric gauge
# HELP another_metric Just an example.
another_metric 2398.283
EOF
```

curl -X DELETE http://pushgateway.example.org:9091/metrics/job/some_job/instance/some_instance

- prometheus は、scrape したメトリクスに job ラベルと instance ラベルを添付する
- scrape config に、honor_labels: true とすると、pushgateway 側のラベルが優先される

- /metrics/job/[jobName] にたいしてもメトリクスを登録できるが、instance=""で登録され、prometheus による上書きを防止する

- /metrics エンドポイントで公開される

- --persistence.file を付けないと永続化されないので注意

- /metrics/job/<JOB_NAME>{/<LABEL_NAME>/<LABEL_VALUE>}

- prometheus は 5 分以内に scrape できなかったメトリクスは存在しなかったように動作する
- label として

- timestamp について
- some_metric{instance="some_instance",job="some_job",label="val1"} 42
- push_time_seconds{instance="some_instance",job="some_job"} 1.6307177336825004e+09
- push_failure_time_seconds{instance="some_instance",job="some_job"} 0
