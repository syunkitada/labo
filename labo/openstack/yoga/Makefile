image:
	sudo docker build -t labo/ubuntu22-openstack-yoga .

run:
	docker run -d --cgroup-parent=docker.slice --cgroupns private --privileged -v .:/home/host --name openstack-yoga labo/ubuntu22-openstack-yoga

clean:
	docker stop openstack-yoga && docker rm openstack-yoga || echo "already cleaned"

bash:
	docker exec -it openstack-yoga bash -c 'source /adminrc && cd && bash || bash'

zsh:
	docker exec -it openstack-yoga bash -c 'source /adminrc && cd && zsh || zsh'

setup:
	docker exec openstack-yoga sh -c 'cd /home/host && ./common.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/keystone && ./setup.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/glance && ./setup.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/glance && ./image-create.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/neutron && ./setup.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/neutron && ./network-create.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/neutron && ./setup-compute.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/placement && ./setup.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/nova && ./setup.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/nova && ./flavor-create.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/nova && ./setup-compute.sh'
	docker exec openstack-yoga sh -c 'cd /home/host/nova && ./server-create.sh'
