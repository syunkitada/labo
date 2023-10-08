image:
	sudo docker build -t labo/ubuntu22-openstack-yoga .

run:
	docker run -d -it --rm --privileged --cap-add=SYS_ADMIN -v .:/home/host -v /sys/fs/cgroup:/sys/fs/cgroup:rw --name openstack-yoga labo/ubuntu22-openstack-yoga

clean:
	docker stop openstack-yoga

bash:
	docker exec -it openstack-yoga bash
