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
  - クラスタリングの例
    - [Configuring Multi-Node Consul Cluster and client For Service Discovery](https://rudhra13.medium.com/configuring-multi-node-consul-cluster-and-client-for-service-discovery-fb7ee0b431fc)
- WAN federation
  - スケーラビリティのための仕組みで、複数DCのServer Agentsをフルメッシュでつなげる
  - Client Agentsの管理は各DCごととのServer Agentsが担当する

## セキュリティ: ACL

- https://developer.hashicorp.com/consul/docs/security/acl
- ACLはリクエストを認証し、リソースへのアクセスの認可を行います
- Consul UI, API, CLIのアクセス制御、サービス間、エージェント間の安全な通信もサポートする
- Tokens
  - https://developer.hashicorp.com/consul/docs/security/acl/tokens
  - Tokenには一つ以上のPoliciesが紐づいている
  - SecretIDフィールド
    - UUID
- Policies
- Roles
- ACLのBootstrap
  - SecretIDを指定することで、最初のTokenを作ることができる
  - API
    - https://developer.hashicorp.com/consul/api-docs/acl#bootstrap-acls
  - Ansible
    - https://docs.ansible.com/ansible/latest/collections/community/general/consul_acl_bootstrap_module.html#ansible-collections-community-general-consul-acl-bootstrap-module
