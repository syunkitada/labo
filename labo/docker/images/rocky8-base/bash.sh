docker run -d -it --rm --privileged --cap-add=SYS_ADMIN -v /sys/fs/cgroup:/sys/fs/cgroup:ro --name rocky8 labo/rocky8-base
