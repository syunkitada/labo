# nfs utils


def make_nfs(c, spec):
    c.sudo(f"mkdir -p {spec['path']}", hide=True)
    c.sudo(f"chown nobody.nogroup {spec['path']}", hide=True)

    exports_strs = []
    exports_strs.append(f"{spec['path']} 127.0.0.1/8(rw,sync,fsid=0,crossmnt,no_subtree_check,insecure,all_squash)")
    for export in spec["exports"]:
        exports_strs.append(f"{spec['path']} {export}(rw,sync,fsid=0,crossmnt,no_subtree_check,insecure,all_squash)")

    c.sudo(
        """sh -c 'cat << EOS | sudo tee /etc/exports
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

{}
EOS'""".format(
            "\n".join(exports_strs)
        ),
        hide=True,
    )

    # exportfs
    # NFSでエクスポートしているファイルシステムのテーブルを管理するために使うコマンド
    # -a すべてのディレクトリをexport/unexportする
    # -r すべてのディレクトリを再exportする、/var/lib/nfs/xtabを/etc/exportsと同期させる
    c.sudo("exportfs -ra", hide=True)

    c.sudo(f"mount -t nfs localhost:/ {spec['local_path']}", hide=True)
