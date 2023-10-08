#!/bin/bash -ex

docker run -d -it --rm --privileged --cap-add=SYS_ADMIN -v /sys/fs/cgroup:/sys/fs/cgroup:rw --name ubuntu22 labo/ubuntu22-base
docker exec -it ubuntu22 bash
