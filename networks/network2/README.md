# network2

sudo docker run -it --privileged -d --rm --network none --name leaf1 centos7-node:latest sh
sudo docker run -it --privileged -d --rm --network none --name hv1 centos7-node:latest sh

sudo mkdir -p /var/run/netns

PID=`sudo docker inspect --format '{{.State.Pid}}' leaf1`
sudo ln -sfT /proc/$PID/ns/net /var/run/netns/leaf1

PID=`sudo docker inspect --format '{{.State.Pid}}' hv1`
sudo ln -sfT /proc/$PID/ns/net /var/run/netns/hv1

sudo ip netns exec test1 ip a

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
```

sudo ip netns add test0

sudo ip link set tier11-veth netns tier11 up

show bgp summary
