# Monitoring

- grafana: http://dev01.pm.local.test:3000
  - user: admin, password: admin
- victoriametrics: http://dev01.pm.local.test:8428/vmui
- victoriametrics-vmagent: http://dev01.pm.local.test:8429
- victoriametrics-vmalert: http://dev01.pm.local.test:8880
- kafka-ui: http://dev01.pm.local.test:9090
- alertmanager: http://dev01.pm.local.test:9093
- rustfs: http://dev01.pm.local.test:9001

Prometheus metrics endpoints:

- victoriametrics: http://dev01.pm.local.test:8428/metrics
- victoriametrics-vmagent: http://dev01.pm.local.test:8429/metrics
- victoriametrics-vmalert: http://dev01.pm.local.test:8880/metrics
- vector-aggregator: http://dev01.pm.local.test:9599/metrics
- vector-agent: http://dev01.pm.local.test:9598/metrics
- alertmanager: http://dev01.pm.local.test:9093/metrics
- node-exporter: http://dev01.pm.local.test:9100/metrics
