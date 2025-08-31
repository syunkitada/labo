#!/bin/bash -xe

systemctl start openvswitch
 
ovs-vsctl --may-exist add-br {{ spec['vars']['ovs_external_bridge']['name'] }}
ovs-vsctl --may-exist add-br {{ spec['vars']['ovs_vm_bridge']['name'] }}

ex_to_int={{ spec['vars']['ovs_external_bridge']['name']}}_{{ spec['vars']['ovs_vm_bridge']['name']}}
int_to_ex={{ spec['vars']['ovs_vm_bridge']['name']}}_{{ spec['vars']['ovs_external_bridge']['name']}}

ovs-vsctl --may-exist add-port {{ spec['vars']['ovs_external_bridge']['name']}} ${ex_to_int} \
    -- set interface ${ex_to_int} type=patch options:peer=${int_to_ex}

ovs-vsctl --may-exist add-port {{ spec['vars']['ovs_vm_bridge']['name']}} ${int_to_ex} \
    -- set interface ${int_to_ex} type=patch options:peer=${ex_to_int}

{% for interface in spec['vars']['ovs_external_interfaces'] %}
ovs-vsctl --may-exist add-port {{ spec['vars']['ovs_external_bridge']['name']}} ${int_to_ex}_{{ loop.index }} \
    -- set interface ${int_to_ex}_{{ loop.index }} type=patch options:peer=${ex_to_int}_{{ loop.index }}

bgp_interface="bgp{{ loop.index }}"
interface_name="{{ spec['vars']['ovs_external_bridge']['name'] }}-${bgp_interface}"

if ! ip addr show dev ${bgp_interface}; then
  ip link add ${bgp_interface} type veth peer name ${interface_name}
fi
ip link set dev ${interface_name} mtu 9000
ip link set ${interface_name} up
ethtool -K ${interface_name} tso off tx off
ip link set dev ${bgp_interface} up
ethtool -K ${bgp_interface} tso off tx off

ovs-vsctl --no-wait --may-exist add-port {{ spec['vars']['ovs_external_bridge']['name'] }} ${interface_name})

{% endfor %}


{% for port in spec['vars']['ovs_vm_bridge']['ports'] %}
ovs-vsctl --may-exist add-port {{ spec['vars']['ovs_vm_bridge']['name'] }} {{port.name}}
{% endfor %}