#!/bin/bash -x

COMMAND="${*:-help}"

function help() {
	cat <<EOS
setup
EOS
}

isCentos=false
if grep 'CentOS' /etc/os-release; then
	isCentos=true
fi

isUbuntu=false
grep 'Ubuntu' /etc/os-release
if grep 'Ubuntu' /etc/os-release; then
	isUbuntu=true
fi

function setup() {
	if "$isCentos"; then
		sudo yum install -y yum-utils
		sudo yum-config-manager \
			--add-repo \
			https://download.docker.com/linux/centos/docker-ce.repo
		sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose
	fi

	if "$isUbuntu"; then
		sudo apt-get update
		sudo apt-get install -y \
			apt-transport-https \
			ca-certificates \
			curl \
			gnupg \
			lsb-release

		sudo install -m 0755 -d /etc/apt/keyrings
		curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
		sudo chmod a+r /etc/apt/keyrings/docker.gpg
		echo \
			"deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
"$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
		sudo apt-get update
		sudo apt-get install -y docker-ce docker-ce-cli containerd.io
	fi

	sudo systemctl restart docker
}

function setup-registry() {
	name=docker-registry
	sudo docker ps | grep " ${name}$" ||
		( 
			(sudo docker ps --all | grep " ${name}$" && sudo docker rm "${name}" || echo "${name} not found") &&
				sudo docker run -d --rm --net host --name ${name} \
					-v "/var/lib/docker-registry":/var/lib/registry \
					registry:2
		)
}

$COMMAND
