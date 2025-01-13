all:
	@make setup

setup:
	sudo docker compose up -d
	sudo modprobe openvswitch
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-db.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-memcached.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-rabbitmq.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-common.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-keystone.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-glance.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-neutron.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-placement.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-nova.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-openstack-data.sh
	sudo docker exec -i openstack-2024-2 /opt/openstack/scripts/setup-compute.sh

clean:
	rm -rf .venv
	sudo docker compose down
