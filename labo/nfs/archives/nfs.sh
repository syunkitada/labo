#!/bin/bash -xe

# This script is deprecated.
# The recommended procedure is as follows.
# $ sudo -E .venv/bin/ansible-playbook ansible/playbooks/nfs/main.yaml

COMMAND="${@:-help}"

function help() {
	cat <<EOS
setup
EOS
}

function setup() {
	sudo apt install -y nfs-kernel-server nfs-common

	sudo mkdir -p /var/nfs/exports
	sudo chown nobody.nogroup /var/nfs/exports

	cat <<EOS | sudo tee /etc/exports
# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
#
# Example for NFSv2 and NFSv3:
# /srv/homes       hostname1(rw,sync,no_subtree_check) hostname2(ro,sync,no_subtree_check)
#
# Example for NFSv4:
# /srv/nfs4        gss/krb5i(rw,sync,fsid=0,crossmnt,no_subtree_check)
# /srv/nfs4/homes  gss/krb5i(rw,sync,no_subtree_check)
#

/var/nfs/exports 127.0.0.1/8(rw,sync,fsid=0,crossmnt,no_subtree_check,insecure,all_squash)
/var/nfs/exports 10.0.0.0/8(rw,sync,fsid=0,crossmnt,no_subtree_check,insecure,all_squash)
/var/nfs/exports 172.16.0.0/12(rw,sync,fsid=0,crossmnt,no_subtree_check,insecure,all_squash)
/var/nfs/exports 192.168.0.0/16(rw,sync,fsid=0,crossmnt,no_subtree_check,insecure,all_squash)
EOS

	# exportfs
	# NFSでエクスポートしているファイルシステムのテーブルを管理するために使うコマンド
	# -a すべてのディレクトリをexport/unexportする
	# -r すべてのディレクトリを再exportする、/var/lib/nfs/xtabを/etc/exportsと同期させる
	sudo exportfs -ra

	sudo mount -t nfs localhost:/ /mnt/nfs
}

$COMMAND
