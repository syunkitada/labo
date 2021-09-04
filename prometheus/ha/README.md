# Prometheus HA 構成

## システム構成

```
exporters <-- pull metrics -- prometheus-scraper1-1 ＼
                           ×
exporters <-- pull metrics -- prometheus-scraper1-2 ＼

exporters <-- pull metrics -- prometheus-scraper2-1 ＼
                           ×
exporters <-- pull metrics -- prometheus-scraper2-2 <- pull metrics -- prometheus-federator1-1 -- notify --> alertmanager1-1 -- notify -->
                                                                    ×                          ×               |
exporters <-- pull metrics -- prometheus-scraper3-1 <- pull metrics -- prometheus-federator1-2 -- notify --> alertmanager1-2 -- notify -->
                           ×                                                                                    |
exporters <-- pull metrics -- prometheus-scraper3-2 ／                                                           |
                                                                                                                 |
exporters <-- pull metrics -- prometheus-scraper4-1 ／                                                           |
                           ×                                                                                    |
exporters <-- pull metrics -- prometheus-scraper4-2 ／                                                           |
                                                                                                                 |
pushers -- push metrics --> vip -- pushgateway1-1   ／                                                           |
pushers -- push metrics -->     ＼ pushgateway1-2   ／                                                           |
                                                                                                                 |
pushers -- push metrics --> vip -- pushgateway2-1   ／                                                           |
pushers -- push metrics -->     ＼ pushgateway2-2   ／                                                           |
                                                                                                                 |
                                                                                                             alertmanager1-3
                                                                                                                 |
                                                                                                             alertmanager1-4
```
