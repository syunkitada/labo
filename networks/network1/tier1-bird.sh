#!/bin/bash -e

cat << EOT | sudo tee /etc/bird/tier11-bird.conf
router id 10.1.0.11;

log syslog { debug, trace, info, remote, warning, error, auth, fatal, bug };
log stderr all;
log "/var/log/tier11-bird.log" all;

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
  local as 65100;
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
  export all;
}

protocol bgp Mesh_10_1_0_12 from bgp_template {
  neighbor 10.1.0.12 as 65200;
}

protocol bgp Mesh_10_1_0_13 from bgp_template {
  neighbor 10.1.0.13 as 65300;
}

protocol bgp Mesh_10_110_0_11 from bgp_template {
  neighbor 10.110.0.11 as 65110;
}

protocol bgp Mesh_10_110_0_12 from bgp_template {
  neighbor 10.110.0.12 as 65120;
}
EOT


cat << EOT | sudo tee /etc/bird/tier12-bird.conf
router id 10.1.0.12;

log syslog { debug, trace, info, remote, warning, error, auth, fatal, bug };
log stderr all;
log "/var/log/tier12-bird.log" all;

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
  local as 65200;
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
  export all;
}

protocol bgp Mesh_10_1_0_11 from bgp_template {
  neighbor 10.1.0.11 as 65100;
}

protocol bgp Mesh_10_1_0_13 from bgp_template {
  neighbor 10.1.0.13 as 65300;
}

protocol bgp Mesh_10_120_0_11 from bgp_template {
  neighbor 10.120.0.11 as 65210;
}

protocol bgp Mesh_10_120_0_12 from bgp_template {
  neighbor 10.120.0.12 as 65220;
}
EOT


cat << EOT | sudo tee /etc/bird/tier13-bird.conf
router id 10.1.0.13;

log syslog { debug, trace, info, remote, warning, error, auth, fatal, bug };
log stderr all;
log "/var/log/tier13-bird.log" all;

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
  local as 65300;
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
  export all;
}

protocol bgp Mesh_10_1_0_11 from bgp_template {
  neighbor 10.1.0.11 as 65100;
}

protocol bgp Mesh_10_1_0_12 from bgp_template {
  neighbor 10.1.0.12 as 65200;
}
EOT



sudo ip netns exec tier11 bird -c /etc/bird/tier11-bird.conf -P /var/run/tier11-bird.pid -s /var/run/tier11-bird.ctl
sudo ip netns exec tier12 bird -c /etc/bird/tier12-bird.conf -P /var/run/tier12-bird.pid -s /var/run/tier12-bird.ctl
sudo ip netns exec tier13 bird -c /etc/bird/tier13-bird.conf -P /var/run/tier13-bird.pid -s /var/run/tier13-bird.ctl

sudo ip netns exec tier11 netstat -an
sudo ip netns exec tier12 netstat -an
sudo ip netns exec tier13 netstat -an

# birdcl -s /var/run/tier11-bird.ctl
# birdcl -s /var/run/tier12-bird.ctl
# birdcl -s /var/run/tier13-bird.ctl
