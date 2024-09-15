# SigNoz

- SigNoz
  - About
    - SigNoz is an open-source observability tool that helps you monitor your applications and troubleshoot problems.
    - It provides traces, metrics, and logs under a single pane of glass.
    - It is available as both an open-source software and a cloud offering.
  - Github: https://github.com/SigNoz/signoz
  - License: eeディレクトリ以外はMIT
    - https://github.com/SigNoz/signoz/blob/develop/LICENSE
    - eeディレクトリは、SigNoz Enterprise
      - https://github.com/SigNoz/signoz/blob/develop/ee/LICENSE
  - Doc: https://signoz.io/docs/introduction/
- ClickHouse
  - About
    - ClickHouse is a high-performance, column-oriented SQL database management system (DBMS) for online analytical processing (OLAP).
    - It is available as both an open-source software and a cloud offering.
    - SigNozはDBMSとしてClickHouseを利用しています
  - Github: https://github.com/ClickHouse/ClickHouse
  - Doc: https://clickhouse.com/docs/en/intro
  - License: Apache License 2.0
    - https://github.com/ClickHouse/ClickHouse/blob/master/LICENSE

## Architecture

- https://signoz.io/docs/architecture/
- フロントエンドはReactで開発されてる
  - antが使われてる？
    - https://github.com/ant-design/ant-design
