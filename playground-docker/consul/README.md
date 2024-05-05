# Consul

## Architecture

- https://developer.hashicorp.com/consul/docs/architecture
- Datacenter(DC)
  - 1DC = 1クラスタ で、consulの最小構成単位のこと
  - 1DCは、複数のconsul serverノード群(Server Agents)と、複数のconsul clientノード群(Client Agents)から構成される
  - Server Agents
    - 3, 5 台の奇数台数で構成され、フルメッシュでつながる
    - 1つのleader と 複数のfollowerから構成される
      - leaderは自動で選定される
  - Client Agents
    - ノード数に制限はないが、1つのクラスタあたりの最大数は5000台が推奨とされている
- WAN federation
  - スケーラビリティのための仕組みで、複数DCのServer Agentsをフルメッシュでつなげる
  - Client Agentsの管理は各DCごととのServer Agentsが担当する

## ACL
