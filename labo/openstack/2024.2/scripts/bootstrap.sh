#!/bin/bash -xe

source iamrc

USER_NAME="debug"
TEAM_NAME="team1"
ORGANIZATION_NAME="organization1"
PROJECT_NAME="project1"

if openstack project list --tags Team -f value -c ID -c Name | grep " ${TEAM_NAME}$"; then
	echo "${TEAM_NAME} already exists"
else
	openstack project create --tag Team ${TEAM_NAME} --domain default
fi

if openstack project list --tags Organization -f value -c ID -c Name | grep " ${ORGANIZATION_NAME}$"; then
	echo "${ORGANIZATION_NAME} already exists"
else
	openstack project create --tag Organization ${ORGANIZATION_NAME} --domain default
fi

ORGANIZATION_ID=$(openstack project list --tags Organization -f value -c ID -c Name | grep " ${ORGANIZATION_NAME}$" | awk '{print $1}')

if openstack project list -f value -c ID -c Name | grep " ${PROJECT_NAME}$"; then
	echo "${PROJECT_NAME} already exists"
else
	openstack project create ${PROJECT_NAME} --property "organization_id=${ORGANIZATION_ID}" --domain default
fi

TEAM_ID=$(openstack project list --tags Team -f value -c ID -c Name | grep " ${TEAM_NAME}$" | awk '{print $1}')

openstack role add --project "${TEAM_ID}" --user "${USER_NAME}" member

openstack role assignment list

openstack role add --project "${PROJECT_ID}" --group "${TEAM_ID}" _group
