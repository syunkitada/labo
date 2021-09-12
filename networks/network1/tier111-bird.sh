#!/bin/sh

cat << EOT | sudo tee /etc/bird/as1111-bird.conf
router id 10.111.0.11;

log syslog { debug, trace, info, remote, warning, error, auth, fatal, bug };
log stderr all;
log "/var/log/as1111-bird.log" all;

# Configure synchronization between routing tables and kernel.
protocol kernel {
  learn;             # Learn all alien routes from the kernel
  persist;           # Don't remove routes on bird shutdown
  scan time 2;       # Scan kernel routing table every 2 seconds
  import all;
  export all;
  graceful restart;  # Turn on graceful restart to reduce potential flaps in
                     # routes when reloading BIRD configuration.  With a full
                     # automatic mesh, there is no way to prevent BGP from
                     # flapping since multiple nodes update their BGP
                     # configuration at the same time, GR is not guaranteed to
                     # work correctly in this scenario.
}

protocol device {
  scan time 10; # Scan interfaces every 10 seconds
}

protocol direct {
  interface "*veth*", "*"; # Restrict network interfaces it works with
}

template bgp bgp_template {
  local as 65111;
  multihop;

  hold time 240;
  startup hold time 240;
  connect retry time 120;
  keepalive time 80;       # defaults to hold time / 3
  start delay time 5;      # How long do we wait before initial connect
  error wait time 60, 300; # Minimum and maximum time we wait after an error (when consecutive
                           # errors occur, we increase the delay exponentially ...
  error forget time 300;   # ... until this timeout expires)
  disable after error;     # Disable the protocol automatically when an error occurs
  next hop self;           # Disable next hop processing and always advertise our local address as nexthop

  graceful restart;
  import all;
  export filter {
    accept;
  };
}

protocol bgp Mesh_10_111_0_10 from bgp_template {
  neighbor 10.111.0.10 as 65110;
}
EOT

sudo ip netns exec as1111 bird -c /etc/bird/as1111-bird.conf -P /var/run/as1111-bird.pid -s /var/run/as1111-bird.ctl

sudo ip netns exec as1111 netstat -an
