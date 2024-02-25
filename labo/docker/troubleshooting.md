# docker troubleshooting

## Failed to create /../../init.scope control group: Operation not permitted

- 環境
  - HOST
    - OS: ubuntu:22.04
    - cgroup: v2
  - IMAGE
    - FROM ubuntu:22.04
    - ENTRYPOINT ["/usr/sbin/init"]
- 類似エラー
  - https://github.com/moby/moby/issues/42275

事象

```
# 以下のオプションでdockerイメージを起動
$ docker run -d --privileged --cap-add=SYS_ADMIN -v .:/home/host -v /sys/fs/cgroup:/sys/fs/cgroup:rw --name openstack-yoga labo/ubuntu22-openstack-yoga

# dockerにclangをinstallするとコンテナが落ちる
$ sudo docker exec -it dummy bash
$ apt install -y clang
...
Unpacking libc6:amd64 (2.35-0ubuntu3.4) over (2.35-0ubuntu3.3) ...
Setting up libc6:amd64 (2.35-0ubuntu3.4) ...
debconf: unable to initialize frontend: Dialog
debconf: (No usable dialog-like program is installed, so the dialog based frontend cannot be used. at /usr/share/perl5/Debconf/FrontEnd/Dialog.pm line 78.)
debconf: falling back to frontend: Readline

$ docker logs dummy
Failed to create /../../init.scope control group: Operation not permitted
Failed to allocate manager object: Operation not permitted
[!!!!!!] Failed to allocate manager object.
Exiting PID 1...
```

解決

以下ように--cgroup-parent=docker.slice --cgroupns private を指定してコンテナ起動することで回避できます。

```
$ docker run -d --cgroup-parent=docker.slice --cgroupns private --privileged -v .:/home/host --name openstack-yoga labo/ubuntu22-openstack-yoga
```

## memo

- [Fedora 38: Cannot use cgroupv1 due to systemd-oom](https://discussion.fedoraproject.org/t/fedora-38-cannot-use-cgroupv1-due-to-systemd-oom/82902)

```
Jan 28 06:52:15 rocky8-test-n1 systemd[1]: Started The Apache HTTP Server.
Jan 28 06:52:15 rocky8-test-n1 httpd[88]: Server configured, listening on: port 80
Jan 28 06:52:15 rocky8-test-n1 systemd[1]: httpd.service: Main process exited, code=exited, status=1/FAILURE
Jan 28 06:52:15 rocky8-test-n1 systemd[1]: httpd.service: Killing process 89 (httpd) with signal SIGKILL.
Jan 28 06:53:45 rocky8-test-n1 systemd[1]: httpd.service: Processes still around after SIGKILL. Ignoring.
Jan 28 06:53:45 rocky8-test-n1 systemd[1]: httpd.service: Failed with result 'exit-code'.
```
