#!/bin/bash -e

cd "$(dirname $0)/../"

function create() {
	if [ $# != 1 ]; then
		echo "require 1 arg"
		help
		exit 1
	fi

	IMAGE_NAME=${1:?}
	DOCKER_FILE="./images/${IMAGE_NAME}/Dockerfile"

	if [ -e "${DOCKER_FILE}" ]; then
		sudo docker build -t "local/${IMAGE_NAME}" ./images --file "${DOCKER_FILE}"
	else
		echo "
IMAGE_NAME=${IMAGE_NAME}
Dockerfile is not found: ${DOCKER_FILE}

Available images are following."
		list
		exit 1
	fi
}

function list() {
	for image in $(ls ./images); do
		echo "${image}"
	done
}

function help() {
	echo "
create [image_name]
list
"
}

if [ $# != 0 ]; then
	"${@}"
else
	help
fi
