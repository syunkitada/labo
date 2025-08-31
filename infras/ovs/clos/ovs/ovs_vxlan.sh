#!/bin/bash -xe

systemctl start openvswitch
 
ovs-vsctl --may-exist add-br {{ spec['vars']['ovs_external_bridge']['name'] }}

ip link set up {{ spec['vars']['ovs_external_bridge']['name'] }}
result=$(ip addr show dev {{ spec['vars']['ovs_external_bridge']['name'] }})

{% if 'local_ip' in spec['vars']['ovs_external_bridge'] %}
if [[ ! "$result" =~ "inet {{ spec['vars']['ovs_external_bridge']['local_ip'] }}/32" ]]; then
  ip addr add {{ spec['vars']['ovs_external_bridge']['local_ip'] }}/32 dev br-ex
fi

result=$(ip rule show)
if [[ ! "$result" =~ "from {{ spec['vars']['ovs_external_bridge']['local_ip'] }} table 200" ]]; then
  ip rule add from {{ spec['vars']['ovs_external_bridge']['local_ip'] }} table 200 prio 25
  ip route replace table 200 0.0.0.0/0 dev br-ex src {{ spec['vars']['ovs_external_bridge']['local_ip'] }}
fi
{% endif %}